"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from objects import Radioactivity, Waste
from utils import Color, Direction, Position
from agent import Agent, Inventory

if TYPE_CHECKING:
    from model import RobotMission


class CasePerception:
    def __init__(self, color: Color, waste: Waste | None, agent: Agent | None) -> None:
        self.waste = waste
        self.agent = agent
        self.color = color


class Perception:
    def __init__(
        self,
        cases: dict[Direction, CasePerception],
        inventory: Inventory,
        color: Color,
        dump_pos: Position,
        current_pos: Position,
        grid_width: int,
        grid_height: int,
    ) -> None:
        self._cases = cases
        self.inventory = inventory
        self.color = color
        self.dump_pos = dump_pos
        self.current_pos = current_pos
        self.grid_width = grid_width
        self.grid_height = grid_height

    @staticmethod
    def from_agent(model: RobotMission, agent: Agent) -> Perception:
        cases = {}
        pos = agent.get_true_pos()

        for coords in model.grid.get_neighborhood(pos, moore=False, include_center=True):
            _waste = None
            _agent = None
            _color = None

            for cell in model.grid.get_cell_list_contents([coords]):
                if isinstance(cell, Waste):
                    assert _waste is None, "Multiple waste in the same cell"
                    _waste = cell
                elif isinstance(cell, Agent):
                    assert _agent is None, "Multiple agents in the same cell"
                    _agent = cell
                elif isinstance(cell, Radioactivity):
                    assert _color is None, "Multiple radioactivity in the same cell"
                    _color = cell.color

            assert _color is not None, "No radioactivity in the cell"

            cases[Direction.get_direction(pos, coords)] = CasePerception(_color, _waste, _agent)

        return Perception(cases, agent.inventory, agent.color, model.dump_pos, pos, model.grid.width, model.grid.height)

    def __getitem__(self, key: Direction) -> CasePerception:
        return self._cases[key]

    def __iter__(self):
        return iter(self._cases)

    def __contains__(self, key: Direction) -> bool:
        return key in self._cases
