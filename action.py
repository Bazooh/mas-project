"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from objects import Waste
from utils import Color, Direction, Position

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
        model.grid.move_agent(agent, self.get_new_pos(agent.get_true_pos()))

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool:
        new_pos = self.get_new_pos(agent.get_true_pos())

        if model.grid.out_of_bounds(new_pos):
            return False

        if model.is_any_agent_at(new_pos):
            return False

        return agent.color >= model.get_color_at(new_pos)


class Pick(Action):
    def apply(self, model: "RobotMission", agent: "Agent") -> None:
        waste = model.get_waste_at(agent.get_true_pos())

        agent.inventory.append(waste)
        model.grid.remove_agent(waste)

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool:
        if agent.is_inventory_full():
            return False

        return model.is_any_waste_at(agent.get_true_pos())


class Drop(Action):
    def __init__(self, waste: Waste) -> None:
        self.waste = waste

    def apply(self, model: "RobotMission", agent: "Agent") -> None:
        agent.inventory.remove(self.waste)
        model.grid.place_agent(self.waste, agent.get_true_pos())

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool:
        if self.waste not in agent.inventory:
            return False

        return not model.is_any_waste_at(agent.get_true_pos())


class Merge(Action):
    def __init__(self, waste1: Waste, waste2: Waste) -> None:
        self.waste1 = waste1
        self.waste2 = waste2

    def apply(self, model: "RobotMission", agent: "Agent") -> None:
        agent.inventory.remove(self.waste1)
        agent.inventory.remove(self.waste2)

        new_waste = Waste(model, Color(self.waste1.color.value + 1))
        agent.inventory.append(new_waste)

    def can_apply(self, model: "RobotMission", agent: "Agent") -> bool:
        if self.waste1 not in agent.inventory or self.waste2 not in agent.inventory:
            return False

        if self.waste1.color != self.waste2.color:
            return False

        if agent.color != self.waste1.color:
            return False

        return self.waste1.color != Color.RED
