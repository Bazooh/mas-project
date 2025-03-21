"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 15/03/2025
"""

import torch
import torch.nn.functional as F

from typing import TYPE_CHECKING

from action import Action, Drop, Merge, Move, Pick, Wait
from agent import Agent
from knowledge import AllKnowledge
from utils import Color, Direction
from network import Network

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
    def __init__(self, model: "RobotMission", color: Color, training_id: int = 0) -> None:
        super().__init__(model, color)
        self.knowledge = AllKnowledge()
        self.network = Network(24)
        self.network.load_state_dict(torch.load("networks/final.pth"))
        self.training_id = training_id

    def policy_to_choice(self, policy: torch.Tensor) -> int:
        choice = int(torch.argmax(policy).item())

        if 1 <= choice <= 4:
            policy = F.softmax(policy[1:5], dim=0)
            filtered_policy = torch.where(policy > 0.1, policy, 0)
            return int(torch.multinomial(filtered_policy, 1).item()) + 1

        return choice

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
            policy = self.network(self.knowledge.to_tensor())
        return self.deliberate_from_choice(self.policy_to_choice(policy))

    def step_from_choice(self, choice: int) -> int:
        self.action = self.deliberate_from_choice(choice)
        self.perception = self.model.do(self.action, self)
        self.knowledge.update(self.perception)

        return choice
