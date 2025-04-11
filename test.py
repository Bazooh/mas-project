from torchview import draw_graph
import torch.nn.functional as F
import torch.nn as nn
import torch
# model = MemoryNetwork(26)


F.relu = lambda x: x

# dummy_input = torch.randn(1, 2)
# dummy_state = torch.randn(1, 12, 10, 10)


class MixingNetwork(nn.Module):
    def __init__(self, num_agents: int, hidden_dim: int, height: int, width: int) -> None:
        super().__init__()
        self.num_agents = num_agents
        state_dim = 3 * (num_agents + 2)

        self.conv = nn.Conv2d(state_dim, num_agents, 5)

        conv_dim = (height - 4) * (width - 4) * num_agents
        self.hyper_w1 = nn.Linear(conv_dim, num_agents * hidden_dim)
        self.hyper_w2 = nn.Linear(conv_dim, hidden_dim)

        self.hyper_b1 = nn.Linear(conv_dim, hidden_dim)
        self.hyper_b2 = nn.Linear(conv_dim, 1)

    def forward(self, agent_qs: torch.Tensor, state: torch.Tensor) -> torch.Tensor:
        """
        agent_qs: (batch_size, num_agents)
        state: (batch_size, width, height, state_dim)
        """
        batch_size = agent_qs.shape[0]

        conv_state = F.relu(self.conv(state)).view(batch_size, -1)  # (B, N*(h-4)*(w-4))

        w1 = torch.abs(self.hyper_w1(conv_state)).view(batch_size, self.num_agents, -1)  # (B, N, H)
        w2 = torch.abs(self.hyper_w2(conv_state)).view(batch_size, -1, 1)  # (B, H, 1)

        b1 = self.hyper_b1(conv_state).view(batch_size, 1, -1)  # (B, 1, H)
        b2 = self.hyper_b2(conv_state).view(batch_size, 1, 1)  # (B, 1, 1)

        hidden = torch.relu(torch.bmm(agent_qs.unsqueeze(1), w1) + b1)  # (B, 1, H)
        q_total = torch.bmm(hidden, w2) + b2  # (B, 1, 1)

        return q_total.squeeze(1)  # (B, 1) → scalar Q-value


# Draw a clean layer-level graph
graph = draw_graph(MixingNetwork(2, 5, 10, 10), input_size=((1, 2), (1, 12, 10, 10)), save_graph=True)
