"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import mesa

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from knowledge import PositionKnowledge
from action import Action, Move
from perception import Perception
from utils import Color

if TYPE_CHECKING:
    from model import RobotMission


class Agent(mesa.Agent, ABC):
    """An agent with fixed initial wealth."""

    model: "RobotMission"  # type: ignore

    def __init__(self, model: "RobotMission", color: Color, x: int, y: int):
        """initialize a MoneyAgent instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        self.knowledge = PositionKnowledge()
        self.perception = Perception(x, y)
        self.color = color

    def step(self) -> None:
        self.knowledge.update(self.perception)
        action = self.deliberate()
        self.perception = self.model.do(action, self)

    @abstractmethod
    def deliberate(self) -> Action: ...


class RandomAgent(Agent):
    def deliberate(self) -> Action:
        return Move.random()
