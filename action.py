from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from utils import Direction

if TYPE_CHECKING:
    from agent import Agent


class Action(ABC):
    def __init__(self, agent: "Agent") -> None:
        self.model = agent.model
        self.agent = agent

    @abstractmethod
    def apply(self) -> None: ...

    @abstractmethod
    def can_apply(self) -> bool: ...


class Move(Action):
    def __init__(self, agent: "Agent", direction: Direction) -> None:
        super().__init__(agent)
        self.direction = direction

    def apply(self) -> None: ...

    def can_apply(self) -> bool: ...

    @staticmethod
    def random(agent: "Agent") -> "Move":
        return Move(agent, Direction.random())


class Pick(Action):
    def apply(self) -> None: ...

    def can_apply(self) -> bool: ...


class Drop(Action):
    def apply(self) -> None: ...

    def can_apply(self) -> bool: ...


class Merge(Action):
    def apply(self) -> None: ...

    def can_apply(self) -> bool: ...
