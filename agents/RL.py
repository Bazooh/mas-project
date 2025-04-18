"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 15/03/2025
"""

import torch

from typing import TYPE_CHECKING

from action import Action, Drop, Merge, Move, Pick, Wait
from agent import Agent
from knowledge import AllKnowledge
from utils import Color, Direction
from network import MemoryNetwork, Network

if TYPE_CHECKING:
    from model import RobotMission


def action_to_index(action: Action) -> int:
    match action:
        case Wait():
            return 0
        case Move():
            return action.direction.value
        case Pick():
            return 5
        case Drop():
            return 6
        case Merge():
            return 7

    raise ValueError("Invalid action")


class RLAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color, training_id: int = 0, network: Network | None = None) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()

        self.memory = None

        if network is not None:
            self.network = network
        else:
            self.network = MemoryNetwork(26)
            models = {
                Color.GREEN: "networks/greedy_green40000.pth",
                Color.YELLOW: "networks/greedy_yellow40000.pth",
                Color.RED: "networks/greedy_red40000.pth",
            }
            self.network.load_state_dict(torch.load(models[color]))
        self.training_id = training_id

    def policy_to_choice(self, policy: torch.Tensor) -> int:
        return int(torch.argmax(policy).item())

    def deliberate_from_choice(self, choice: int) -> Action:
        match choice:
            case 0:
                return Wait()
            case 1:
                return Move(Direction.UP)
            case 2:
                return Move(Direction.DOWN)
            case 3:
                return Move(Direction.LEFT)
            case 4:
                return Move(Direction.RIGHT)
            case 5:
                return Pick()
            case 6:
                waste = self.inventory.get_highest_waste()
                return Drop(waste) if waste is not None else Wait()
            case 7:
                merge = self.knowledge.try_merge()
                return merge if merge is not None else Wait()

        raise ValueError("Invalid action")

    def deliberate(self) -> Action:
        with torch.no_grad():
            policy, self.memory = self.network(self.knowledge.to_tensor().unsqueeze(0).unsqueeze(0), self.memory)
        return self.deliberate_from_choice(self.policy_to_choice(policy.squeeze(0)))

    def step_from_choice(self, choice: int) -> int:
        self.action = self.deliberate_from_choice(choice)
        self.perception = self.model.do(self.action, self)
        self.knowledge.update(self.perception)

        return choice
