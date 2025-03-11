"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from utils import Direction, Position

if TYPE_CHECKING:
    from agent import Agent
    from model import RobotMission


class Action(ABC):
    @abstractmethod
    def apply(self, model: "RobotMission", agent: "Agent") -> None: ...

    @abstractmethod
    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool: ...


class Wait(Action):
    def apply(self, model: "RobotMission", agent: "Agent") -> None:
        pass

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool:
        return True


class Move(Action):
    def __init__(self, direction: Direction) -> None:
        self.direction = direction

    def get_new_pos(self, pos: Position) -> Position:
        return pos[0] + self.direction.to_coords()[0], pos[1] + self.direction.to_coords()[1]

    def apply(self, model: "RobotMission", agent: "Agent") -> None:
        assert self.can_apply(model, agent), "Trying to apply an invalid action"

        model.grid.move_agent(agent, self.get_new_pos(agent.get_true_pos()))

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool:
        new_pos = self.get_new_pos(agent.get_true_pos())

        if model.grid.out_of_bounds(new_pos):
            return False

        if model.is_any_agent_at(new_pos):
            return False

        return agent.color >= model.get_color_at(new_pos)

    @staticmethod
    def random() -> Move:
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
