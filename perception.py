"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

from mesa.space import MultiGrid

from objects import Radioactivity, Waste
from utils import Color, Direction, Position
from agent import Agent


class CasePerception:
    def __init__(self, color: Color, waste: Waste | None, agent: Agent | None) -> None:
        self.waste = waste
        self.agent = agent
        self.color = color


class Perception:
    def __init__(self, perception: dict[Direction, CasePerception]) -> None:
        self._perception = perception

    @staticmethod
    def from_pos(grid: MultiGrid, pos: Position):
        perception = {}
        for coords in grid.get_neighborhood(pos, moore=False, include_center=True):
            waste = None
            agent = None
            color = None

            for cell in grid.get_cell_list_contents([coords]):
                if isinstance(cell, Waste):
                    assert waste is None, "Multiple waste in the same cell"
                    waste = cell
                elif isinstance(cell, Agent):
                    assert agent is None, "Multiple agents in the same cell"
                    agent = cell
                elif isinstance(cell, Radioactivity):
                    assert color is None, "Multiple radioactivity in the same cell"
                    color = cell.color

            assert color is not None, "No radioactivity in the cell"

            perception[Direction.get_direction(pos, coords)] = CasePerception(color, waste, agent)

        return Perception(perception)

    def __getitem__(self, key: Direction) -> CasePerception:
        return self._perception[key]

    def __contains__(self, key: Direction) -> bool:
        return key in self._perception
