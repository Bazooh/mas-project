"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from utils import Direction

if TYPE_CHECKING:
    from agent import Agent
    from model import RobotMission


class Action(ABC):
    @abstractmethod
    def apply(self, model: "RobotMission", agent: "Agent") -> None: ...

    @abstractmethod
    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool: ...


class Move(Action):
    def __init__(self, direction: Direction) -> None:
        self.direction = direction

    def apply(self, model: "RobotMission", agent: "Agent") -> None: ...

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool: ...

    @staticmethod
    def random() -> "Move":
        return Move(Direction.random())


class Pick(Action):
    def apply(self, model: "RobotMission", agent: "Agent") -> None: ...

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool: ...


class Drop(Action):
    def apply(self, model: "RobotMission", agent: "Agent") -> None: ...

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool: ...


class Merge(Action):
    def apply(self, model: "RobotMission", agent: "Agent") -> None: ...

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool: ...
