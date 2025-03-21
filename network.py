"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 15/03/2025
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class Network(nn.Module):
    """
    Output:
        - 0: Wait
        - 1: Move up
        - 2: Move down
        - 3: Move right
        - 4: Move left
        - 5: Pick
        - 6: Drop
        - 7: Merge
    """

    def __init__(self, input_size: int) -> None:
        super().__init__()
        self.input_size = input_size
        self.fc1 = nn.Linear(input_size, 32)
        self.fc2 = nn.Linear(32, 48)
        self.fc3 = nn.Linear(48, 24)
        self.fc4 = nn.Linear(24, 16)
        self.fc5 = nn.Linear(16, 8)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = F.relu(self.fc4(x))
        x = self.fc5(x)
        return x


class MixingNetwork(nn.Module):
    def __init__(self, num_agents: int, state_dim: int, hidden_dim: int, height: int, width: int) -> None:
        super().__init__()
        self.num_agents = num_agents

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
