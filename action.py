from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from utils import Direction

if TYPE_CHECKING:
    from model import RobotMission


class Action(ABC):
    @abstractmethod
    def apply(self, model: "RobotMission") -> None: ...

    @abstractmethod
    def can_apply(self, model: "RobotMission") -> bool: ...


class Move(Action):
    def __init__(self, direction: Direction) -> None:
        self.direction = direction

    def apply(self, model: "RobotMission") -> None: ...

    def can_apply(self, model: "RobotMission") -> bool: ...

    @classmethod
    def random(cls) -> "Action":
        return cls(Direction.random())


class Pick(Action):
    def apply(self, model: "RobotMission") -> None: ...

    def can_apply(self, model: "RobotMission") -> bool: ...


class Drop(Action):
    def apply(self, model: "RobotMission") -> None: ...

    def can_apply(self, model: "RobotMission") -> bool: ...


class Merge(Action):
    def apply(self, model: "RobotMission") -> None: ...

    def can_apply(self, model: "RobotMission") -> bool: ...
