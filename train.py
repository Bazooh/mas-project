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

from action import Drop, Merge, Pick
from agents.RL import RLAgent
from model import RobotMission, default_agents_params
from network import MixingNetwork, Network
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


class Batch:
    observations: tuple[torch.Tensor]
    states: tuple[torch.Tensor]
    actions: tuple[torch.Tensor]
    next_observations: tuple[torch.Tensor]
    next_states: tuple[torch.Tensor]
    rewards: tuple[torch.Tensor]
    dones: tuple[bool]

    def __init__(self, transitions: list[Transition]):
        self.observations, self.states, self.actions, self.next_observations, self.next_states, self.rewards, self.dones = (
            zip(
                *[
                    (t.observations, t.state, t.actions, t.next_observations, t.next_state, t.reward, t.done)
                    for t in transitions
                ]
            )
        )


class ReplayMemory:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, transition: Transition):
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = transition
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int) -> Batch:
        return Batch(random.sample(self.memory, batch_size))

    def __len__(self):
        return len(self.memory)


def get_observations(rl_agents: list[RLAgent]) -> torch.Tensor:
    return torch.stack([agent.knowledge.to_tensor() for agent in rl_agents])


def compute_reward(model: RobotMission, rl_agents: list[RLAgent], total_reward: torch.Tensor) -> torch.Tensor:
    rewards = torch.zeros((len(rl_agents),))
    for agent in rl_agents:
        reward = 10 * int(isinstance(agent.action, Merge))
        reward += 0.1 * int(
            isinstance(agent.action, Pick)
            and model.is_any_waste_at(agent.get_true_pos())
            and model.get_waste_at(agent.get_true_pos()).color == agent.color
        )
        reward -= int(isinstance(agent.action, Drop) and agent.action.waste.color == agent.color) * 0.2
        reward -= len([waste for waste in agent.inventory if waste.color != agent.color]) * 0.1

        rewards[agent.training_id] = reward
    return rewards


def play(memory: ReplayMemory, network: Network, epsilon: float, epoch: int, save: bool = False, **kwargs) -> dict[str, Any]:
    model = RobotMission(green_agent_model="DQN", yellow_agent_model="DQN", **kwargs)
    rl_agents = [agent for agent in model.get_agents() if isinstance(agent, RLAgent)]

    n_rl_agents = len(rl_agents)

    rl_agents.sort(key=lambda a: a.color)
    for i, agent in enumerate(rl_agents):
        agent.training_id = i

    for agent in rl_agents:
        agent.knowledge.update(agent.perception)

    observations = get_observations(rl_agents)

    state = model.to_tensor()
    total_rewards = torch.zeros((n_rl_agents,))
    actions_ratio = torch.zeros((8,))
    for i in range(100):
        if model.is_done():
            break

        actions = torch.randint(0, 8, (n_rl_agents,), dtype=torch.int64)
        random_mask = torch.rand((n_rl_agents,)) < epsilon

        selected_indices = (~random_mask).nonzero(as_tuple=True)[0]
        if selected_indices.numel() > 0:
            with torch.no_grad():
                q_values = network(observations[selected_indices])
            #     policy = F.softmax(q_values, dim=1)
            # filtered_policy = torch.where(policy > 0.1, policy, 0)
            # actions[selected_indices] = torch.multinomial(filtered_policy, 1).squeeze()

            for i, idx in enumerate(selected_indices):
                best_action = q_values[i].argmax().item()
                if 1 <= best_action <= 4:
                    policy = F.softmax(q_values[i, 1:5])
                    filtered_policy = torch.where(policy > 0.1, policy, 0)
                    actions[idx] = torch.multinomial(filtered_policy, 1).item() + 1
                else:
                    actions[idx] = best_action

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
        rewards = compute_reward(model, rl_agents, total_rewards)
        total_rewards += rewards

        memory.push(Transition(observations, state, actions, new_observations, new_state, rewards, i == 99))

        observations = new_observations
        state = new_state
        if save:
            model.history.append(model.serialize())

    if save:
        model.save(f"simulations/{epoch}.json")

    return {"reward": total_rewards.sum().item(), "actions_ratio": actions_ratio / (100 * n_rl_agents)}


def train(
    network: nn.Module,
    target_network: nn.Module,
    mixing_net: nn.Module,
    optimizer: optim.Optimizer,
    memory: ReplayMemory,
    batch_size: int = 512,
    gamma: float = 0.9,
) -> dict[str, float]:
    if len(memory) < batch_size:
        return {"loss": 0, "q_values": 0}

    batch = memory.sample(batch_size)
    observations = torch.stack(batch.observations)
    states = torch.stack(batch.states)
    actions = torch.stack(batch.actions)
    next_observations = torch.stack(batch.next_observations)
    next_states = torch.stack(batch.next_states)
    rewards = torch.stack(batch.rewards)
    dones = torch.tensor(batch.dones, dtype=torch.float32)

    q_values = network(observations).gather(2, actions.unsqueeze(-1)).squeeze(-1)
    # q_total = mixing_net(q_values, states)
    with torch.no_grad():
        next_actions = network(next_observations).argmax(dim=-1, keepdim=True)
        next_q_values = target_network(next_observations).gather(2, next_actions).squeeze(-1)
        # next_q_total = mixing_net(next_q_values, next_states)
        # mixed_rewards = mixing_net(rewards, states)

    target_q_values = rewards + gamma * next_q_values * (1 - dones.unsqueeze(1))

    loss = F.mse_loss(q_values, target_q_values)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    return {
        "loss": loss.item(),
        "q_values": q_values.mean().item(),
        "q_values_std": q_values.std().item(),
        # "diff": (q_values < target_q_values).float().mean().item(),
    }


def main(use_wandb: bool = True):
    if use_wandb:
        wandb.init(project="robot_mission")

    memory = ReplayMemory(10000)
    network = Network(24)
    # network.load_state_dict(torch.load("agents/checkpoint.pth"))

    target_network = Network(24)
    mix_network = MixingNetwork(3, 15, 32, 10, 10)

    optimizer = optim.Adam(network.parameters(), lr=1e-4)

    agent_params = default_agents_params
    agent_params[Color.GREEN]["network"] = network
    agent_params[Color.YELLOW]["network"] = network

    epochs = 100000
    pbar = tqdm(range(epochs))

    epsilon_start = 0.8
    epsilon_end = 0.1
    epsilon_epochs = epochs * 0.2

    epsilon = epsilon_start
    for i in pbar:
        if i % 100 == 0:
            target_network.load_state_dict(network.state_dict())

        if i % 1000 == 0:
            torch.save(network.state_dict(), f"networks/{i}.pth")

        if i <= epsilon_epochs:
            epsilon -= (epsilon_start - epsilon_end) / epsilon_epochs

        results = play(
            memory,
            network,
            epsilon,
            epoch=i,
            agent_params=agent_params,
            n_green_agents=2,
            n_yellow_agents=1,
            n_red_agents=1,
            save=i % 400 == 0,
        )
        infos = train(network, target_network, mix_network, optimizer, memory)
        actions_ratio = results["actions_ratio"]
        actions_ratio = {actions_to_str[i]: ratio.item() for i, ratio in enumerate(actions_ratio)}

        pbar.set_description(f"Loss: {infos['loss']:.5f}, Reward: {results['reward']:.2f}, Epsilon: {epsilon:.2f}")

        if use_wandb:
            wandb.log({**infos, "epsilon": epsilon, "reward": results["reward"], **actions_ratio})

    torch.save(network.state_dict(), "networks/final.pth")


if __name__ == "__main__":
    main(use_wandb=True)
