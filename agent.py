"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import mesa

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from knowledge import PositionKnowledge
from action import Action, Drop, Merge, Move, Pick
from objects import Waste
from utils import Color, Direction, Position

if TYPE_CHECKING:
    from model import RobotMission
    from perception import Perception


class Agent(mesa.Agent, ABC):
    """An agent with fixed initial wealth."""

    model: "RobotMission"  # type: ignore

    def __init__(self, model: "RobotMission", color: Color, perception: "Perception", inventory_capacity: int) -> None:
        """initialize a MoneyAgent instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        self.knowledge = PositionKnowledge()
        self.perception = perception
        self.color = color
        self.inventory: list[Waste] = []
        self.inventory_capacity = inventory_capacity

    def is_inventory_full(self) -> bool:
        return len(self.inventory) >= self.inventory_capacity

    def get_true_pos(self) -> Position:
        assert self.pos is not None, "Trying to get the position of an agent that is not placed"
        return cast(Position, self.pos)

    def try_merge(self) -> Merge | None:
        mergeable_waste = [waste for waste in self.inventory if waste.color == self.color]
        if len(mergeable_waste) < 2:
            return None

        return Merge(mergeable_waste[0], mergeable_waste[1])

    def try_move(self, direction: Direction) -> Move | None:
        if direction not in self.perception:
            return None

        case = self.perception[direction]
        if case.agent is not None or case.color > self.color:
            return None

        return Move(direction)

    def try_drop(self, waste: Waste) -> Drop | None:
        if waste not in self.inventory:
            return None

        if self.perception[Direction.NONE].waste is not None:
            return None

        return Drop(waste)

    def try_pick(self) -> Pick | None:
        if self.is_inventory_full():
            return None

        case = self.perception[Direction.NONE]
        if case.waste is None:
            return None

        if case.waste.color != self.color:
            return None

        return Pick()

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
