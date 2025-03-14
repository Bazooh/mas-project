"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import mesa

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator, cast

from action import Action, Move
from knowledge import ChickenKnowledge
from objects import Waste
from utils import Color, Direction, Position

if TYPE_CHECKING:
    from model import RobotMission
    from perception import Perception


class Inventory:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.wastes: list[Waste] = []

    def is_full(self) -> bool:
        return len(self.wastes) >= self.capacity

    def is_empty(self) -> bool:
        return len(self.wastes) == 0

    def add(self, waste: Waste) -> None:
        self.wastes.append(waste)

    def remove(self, waste: Waste) -> None:
        self.wastes.remove(waste)

    def __contains__(self, waste: Waste) -> bool:
        return waste in self.wastes

    def __iter__(self) -> Iterator[Waste]:
        return iter(self.wastes)


class Agent(mesa.Agent, ABC):
    """An agent with fixed initial wealth."""

    model: "RobotMission"  # type: ignore

    def __init__(self, model: "RobotMission", color: Color, inventory_capacity: int) -> None:
        """initialize a MoneyAgent instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        self.knowledge = ChickenKnowledge()
        self.perception: Perception
        self.color = color
        self.inventory = Inventory(inventory_capacity)
        self.inventory_capacity = inventory_capacity

    def init_perception(self, perception: "Perception") -> None:
        self.perception = perception

    def get_true_pos(self) -> Position:
        assert self.pos is not None, "Trying to get the position of an agent that is not placed"
        return cast(Position, self.pos)

    def step(self) -> None:
        self.knowledge.update(self.perception)
        action = self.deliberate()
        self.perception = self.model.do(action, self)

    @abstractmethod
    def deliberate(self) -> Action: ...


class RandomAgent(Agent):
    def deliberate(self) -> Action:
        return Move(Direction.random())


GreenAgent = RandomAgent
YellowAgent = RandomAgent
RedAgent = RandomAgent
