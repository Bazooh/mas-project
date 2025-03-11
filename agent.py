"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import mesa

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from knowledge import Knowledge

if TYPE_CHECKING:
    from model import RobotMission, Action


class Agent(mesa.Agent, ABC):
    """An agent with fixed initial wealth."""

    model: "RobotMission"  # type: ignore

    def __init__(self, model: "RobotMission"):
        """initialize a MoneyAgent instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        self.knowledge = Knowledge()
        self.perception = {}

    def step(self) -> None:
        self.knowledge.update(self.perception)
        action = self.deliberate()
        self.perception = self.model.do(action)

    @abstractmethod
    def deliberate(self) -> Action: ...


class RandomAgent(Agent):
    def deliberate(self) -> Action:
        return Action.random()
