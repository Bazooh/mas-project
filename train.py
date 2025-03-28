"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 15/03/2025
"""

import random
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import wandb

from typing import Any
from tqdm import tqdm

from action import Merge
from agents.RL import RLAgent
from model import RobotMission, default_agents_params
from network import MemoryNetwork, MixingNetwork, Network
from utils import Color


actions_to_str = {0: "Wait", 1: "Move UP", 2: "Move DOWN", 3: "Move LEFT", 4: "Move RIGHT", 5: "Pick", 6: "Drop", 7: "Merge"}


class Transition:
    def __init__(
        self,
        observations: torch.Tensor,
        state: torch.Tensor,
        actions: torch.Tensor,
        next_observations: torch.Tensor,
        next_state: torch.Tensor,
        reward: torch.Tensor,
        done: bool,
    ):
        self.observations = observations
        self.state = state
        self.actions = actions
        self.next_observations = next_observations
        self.next_state = next_state
        self.reward = reward
        self.done = done


class Game:
    def __init__(self, transitions: list[Transition], final_observation: torch.Tensor, final_state: torch.Tensor) -> None:
        self.observations = torch.stack([transition.observations for transition in transitions] + [final_observation])
        self.state = torch.stack([transition.state for transition in transitions] + [final_state])
        self.actions = torch.stack([transition.actions for transition in transitions])
        self.rewards = torch.stack([transition.reward for transition in transitions])
        self.done = torch.tensor([transition.done for transition in transitions], dtype=torch.float32)


class Batch:
    observations: torch.Tensor
    states: torch.Tensor
    actions: torch.Tensor
    next_observations: torch.Tensor
    next_states: torch.Tensor
    rewards: torch.Tensor
    dones: torch.Tensor

    def __init__(self, games: list[Game], seq_size: int) -> None:
        assert seq_size <= 100, "Sequence size must be less than or equal to 100"

        start_idx = random.randint(0, 100 - seq_size)

        all_observations = torch.stack(
            [game.observations[start_idx : start_idx + seq_size + 1] for game in games]
        ).transpose(1, 2)
        all_states = torch.stack([game.state[start_idx : start_idx + seq_size + 1] for game in games]).transpose(1, 2)

        self.observations = all_observations[:, :, :-1]
        self.states = all_states[:, :, :-1]
        self.actions = torch.stack([game.actions[start_idx : start_idx + seq_size] for game in games]).transpose(1, 2)
        self.next_observations = all_observations[:, :, 1:]
        self.next_states = all_states[:, :, 1:]
        self.rewards = torch.stack([game.rewards[start_idx : start_idx + seq_size] for game in games]).transpose(1, 2)
        self.dones = torch.stack([game.done[start_idx : start_idx + seq_size] for game in games])


class ReplayMemory:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.memory: list[Game] = []
        self.position = 0

    def push(self, game: Game):
        if len(self.memory) < self.capacity:
            self.memory.append(game)
        else:
            self.memory[self.position] = game
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int, seq_size: int) -> Batch:
        return Batch(random.sample(self.memory, batch_size), seq_size)

    def __len__(self):
        return len(self.memory)


def get_observations(rl_agents: list[RLAgent]) -> torch.Tensor:
    return torch.stack([agent.knowledge.to_tensor() for agent in rl_agents])


def compute_reward(model: RobotMission, rl_agents: list[RLAgent]) -> torch.Tensor:
    rewards = torch.zeros((len(rl_agents),))
    for agent in rl_agents:
        rewards[agent.training_id] = int(isinstance(agent.action, Merge))
    return rewards


def play(
    memory: ReplayMemory,
    green_net: MemoryNetwork,
    yellow_net: MemoryNetwork,
    red_net: MemoryNetwork,
    epsilon: float,
    epoch: int,
    n_green_agents: int,
    n_yellow_agents: int,
    n_red_agents: int,
    agent_params: dict[Color, dict[str, Any]],
    save: bool = False,
) -> dict[str, Any]:
    model = RobotMission(
        green_agent_model="DQN",
        yellow_agent_model="DQN",
        red_agent_model="DQN",
        n_green_agents=n_green_agents,
        n_yellow_agents=n_yellow_agents,
        n_red_agents=n_red_agents,
        agent_params=agent_params,
    )
    rl_agents = [agent for agent in model.get_agents() if isinstance(agent, RLAgent)]
    n_rl_agents = len(rl_agents)

    transitions: list[Transition] = []

    rl_agents.sort(key=lambda a: a.color)
    for i, agent in enumerate(rl_agents):
        agent.training_id = i

    for agent in rl_agents:
        agent.knowledge.update(agent.perception)

    observations = get_observations(rl_agents)

    green_hiddens = None
    yellow_hiddens = None
    red_hiddens = None

    state = model.to_tensor()
    total_reward = torch.zeros((len(rl_agents),))
    actions_ratio = torch.zeros((8,))
    for i in range(100):
        if model.is_done():
            break

        actions = torch.randint(0, 8, (n_rl_agents,), dtype=torch.int64)
        green_mask = torch.rand((n_green_agents,)) < epsilon
        yellow_mask = torch.rand((n_yellow_agents,)) < epsilon
        red_mask = torch.rand((n_red_agents,)) < epsilon
        green_selected_indices = (~green_mask).nonzero(as_tuple=True)[0]
        yellow_selected_indices = (~yellow_mask).nonzero(as_tuple=True)[0] + n_green_agents
        red_selected_indices = (~red_mask).nonzero(as_tuple=True)[0] + n_green_agents + n_yellow_agents

        green_hiddens = select_best_action(green_net, observations, actions, green_selected_indices, green_hiddens)
        yellow_hiddens = select_best_action(yellow_net, observations, actions, yellow_selected_indices, yellow_hiddens)
        red_hiddens = select_best_action(red_net, observations, actions, red_selected_indices, red_hiddens)

        agents = model.get_agents()
        random.shuffle(agents)
        for agent in agents:
            if isinstance(agent, RLAgent):
                action = agent.step_from_choice(int(actions[agent.training_id].item()))
                actions_ratio[action] += 1
            else:
                agent.step()
        model.step_idx += 1

        new_observations = get_observations(rl_agents)
        new_state = model.to_tensor()
        reward = compute_reward(model, rl_agents)
        total_reward += reward

        transitions.append(Transition(observations, state, actions, new_observations, new_state, reward, i == 99))

        observations = new_observations
        state = new_state
        if save:
            model.history.append(model.serialize())

    memory.push(Game(transitions, observations, state))

    if save:
        model.save(f"simulations/{epoch}.json")

    return {"reward": total_reward.sum(), "actions_ratio": actions_ratio / (100 * n_rl_agents)}


def select_best_action(
    network: MemoryNetwork,
    observations: torch.Tensor,
    actions: torch.Tensor,
    selected_indices: torch.Tensor,
    hiddens: tuple[torch.Tensor, torch.Tensor] | None = None,
) -> tuple[torch.Tensor, torch.Tensor] | None:
    with torch.no_grad():
        q_values, hiddens = network(observations.unsqueeze(1), hiddens)
        q_values = q_values.squeeze(1)

    for i, idx in enumerate(selected_indices):
        best_action = q_values[i].argmax().item()
        actions[idx] = best_action
        # if 1 <= best_action <= 4:
        #     policy = F.softmax(q_values[i, 1:5], dim=0)
        #     filtered_policy = torch.where(policy > 0.1, policy, 0)
        #     actions[idx] = torch.multinomial(filtered_policy, 1).item() + 1
        # else:
        #     actions[idx] = best_action

    return hiddens


def train(
    green_net: MemoryNetwork,
    green_target_net: MemoryNetwork,
    n_green_agents: int,
    yellow_net: MemoryNetwork,
    yellow_target_net: MemoryNetwork,
    n_yellow_agents: int,
    red_net: MemoryNetwork,
    red_target_net: MemoryNetwork,
    n_red_agents: int,
    mixing_net: MixingNetwork,
    optimizer: optim.Optimizer,
    scheduler: optim.lr_scheduler.CosineAnnealingWarmRestarts,
    memory: ReplayMemory,
    batch_size: int = 128,
    gamma: float = 0.9,
    seq_size: int = 20,
) -> dict[str, float]:
    if len(memory) < batch_size:
        return {"loss": 0, "q_values": 0}

    batch = memory.sample(batch_size, seq_size)

    n_agents = n_green_agents + n_yellow_agents + n_red_agents
    state_size = 3 * (n_agents + 2)

    green_slice = slice(0, n_green_agents)
    yellow_slice = slice(n_green_agents, n_green_agents + n_yellow_agents)
    red_slice = slice(n_green_agents + n_yellow_agents, n_agents)

    green_q_values = get_q_values(green_net, batch, green_slice, batch_size, seq_size)
    yellow_q_values = get_q_values(yellow_net, batch, yellow_slice, batch_size, seq_size)
    red_q_values = get_q_values(red_net, batch, red_slice, batch_size, seq_size)
    q_values = (
        torch.cat([green_q_values, yellow_q_values, red_q_values], dim=1).gather(-1, batch.actions.unsqueeze(-1)).squeeze()
    )

    q_total = mixing_net(
        q_values.transpose(1, 2).reshape(batch_size * seq_size, n_agents),
        batch.states.transpose(1, 2).reshape(batch_size * seq_size, state_size, 10, 10),
    ).reshape(batch_size, seq_size)

    with torch.no_grad():
        next_green_q_values = get_next_q_values(green_target_net, batch, green_slice, batch_size, seq_size)
        next_yellow_q_values = get_next_q_values(yellow_target_net, batch, yellow_slice, batch_size, seq_size)
        next_red_q_values = get_next_q_values(red_target_net, batch, red_slice, batch_size, seq_size)
        next_q_values = torch.cat([next_green_q_values, next_yellow_q_values, next_red_q_values], dim=1)
        next_q_total = mixing_net(
            next_q_values.transpose(1, 2).reshape(batch_size * seq_size, n_agents),
            batch.next_states.transpose(1, 2).reshape(batch_size * seq_size, state_size, 10, 10),
        ).reshape(batch_size, seq_size)

    target_q_total = batch.rewards.sum(1) + gamma * next_q_total * (1 - batch.dones)

    loss = F.mse_loss(q_total, target_q_total)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    scheduler.step()

    return {
        "loss": loss.item(),
        "q_values": q_values.mean().item(),
        "q_values_std": q_values.std().item(),
        # "diff": (q_values < target_q_values).float().mean().item(),
    }


def get_q_values(net: MemoryNetwork, batch: Batch, agent_slice: slice, batch_size: int, seq_size: int) -> torch.Tensor:
    return net(batch.observations[:, agent_slice].reshape(-1, seq_size, net.input_size))[0].reshape(
        batch_size, -1, seq_size, 8
    )


def get_next_q_values(
    target_net: MemoryNetwork, batch: Batch, agent_slice: slice, batch_size: int, seq_size: int
) -> torch.Tensor:
    return (
        target_net(batch.next_observations[:, agent_slice].reshape(-1, seq_size, target_net.input_size))[0]
        .reshape(batch_size, -1, seq_size, 8)
        .max(dim=-1)[0]
    )


def main(use_wandb: bool = True):
    if use_wandb:
        wandb.init(project="robot_mission")

    memory = ReplayMemory(10000)

    green_net = MemoryNetwork(26)
    yellow_net = MemoryNetwork(26)
    red_net = MemoryNetwork(26)
    green_target_net = MemoryNetwork(26)
    yellow_target_net = MemoryNetwork(26)
    red_target_net = MemoryNetwork(26)

    n_green_agents = 3
    n_yellow_agents = 0
    n_red_agents = 0

    mix_network = MixingNetwork(n_green_agents + n_yellow_agents + n_red_agents, 32, 10, 10)

    epochs = 100_000

    optimizer = optim.Adam(
        list(green_net.parameters())
        + list(yellow_net.parameters())
        + list(red_net.parameters())
        + list(mix_network.parameters()),
        lr=1e-3,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=epochs, T_mult=2, eta_min=1e-6)

    agent_params = default_agents_params
    agent_params[Color.GREEN]["network"] = green_net
    agent_params[Color.YELLOW]["network"] = yellow_net
    agent_params[Color.RED]["network"] = red_net

    pbar = tqdm(range(epochs))

    epsilon_start = 0.8
    epsilon_end = 0.01
    epsilon_epochs = epochs * 0.2

    epsilon = epsilon_start
    for i in pbar:
        if i % 100 == 0:
            green_target_net.load_state_dict(green_net.state_dict())
            yellow_target_net.load_state_dict(yellow_net.state_dict())
            red_target_net.load_state_dict(red_net.state_dict())

        if i % 1000 == 0:
            torch.save(green_net.state_dict(), f"networks/greedy_green{i}.pth")
            torch.save(yellow_net.state_dict(), f"networks/greedy_yellow{i}.pth")
            torch.save(red_net.state_dict(), f"networks/greedy_red{i}.pth")

        if i <= epsilon_epochs:
            epsilon -= (epsilon_start - epsilon_end) / epsilon_epochs

        results = play(
            memory,
            green_net,
            yellow_net,
            red_net,
            epsilon,
            epoch=i,
            agent_params=agent_params,
            n_green_agents=n_green_agents,
            n_yellow_agents=n_yellow_agents,
            n_red_agents=n_red_agents,
            save=i % 400 == 0,
        )
        infos = train(
            green_net,
            green_target_net,
            n_green_agents,
            yellow_net,
            yellow_target_net,
            n_yellow_agents,
            red_net,
            red_target_net,
            n_red_agents,
            mix_network,
            optimizer,
            scheduler,
            memory,
            seq_size=10,
        )
        actions_ratio = results["actions_ratio"]
        actions_ratio = {actions_to_str[i]: ratio.item() for i, ratio in enumerate(actions_ratio)}

        pbar.set_description(f"Loss: {infos['loss']:.5e}, Reward: {results['reward']:.2f}, Epsilon: {epsilon:.2f}")

        if use_wandb:
            wandb.log({**infos, "epsilon": epsilon, "reward": results["reward"], **actions_ratio})

    torch.save(green_net.state_dict(), "networks/green_final.pth")
    torch.save(yellow_net.state_dict(), "networks/yellow_final.pth")
    torch.save(red_net.state_dict(), "networks/red_final.pth")


if __name__ == "__main__":
    main(use_wandb=True)
