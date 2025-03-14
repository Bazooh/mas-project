"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 14/03/2025
"""

from typing import cast
from mesa.space import MultiGridContent

from agent import Agent
from model import RobotMission
from objects import Waste
from utils import Color


def model_to_n_waste(model: RobotMission) -> dict[Color, int]:
    n_waste = {Color.GREEN: 0, Color.YELLOW: 0, Color.RED: 0}

    for cells, coords in model.grid.coord_iter():
        cells = cast(MultiGridContent, cells)

        for cell in cells:
            if isinstance(cell, Waste):
                n_waste[cell.color] += 1
            elif isinstance(cell, Agent):
                for waste in cell.inventory:
                    n_waste[waste.color] += 1

    return n_waste
