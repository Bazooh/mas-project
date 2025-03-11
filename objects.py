"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import mesa
from typing import TYPE_CHECKING
import random
from utils import Color

if TYPE_CHECKING:
    from model import RobotMission


class Radioactivity(mesa.Agent):
    model: "RobotMission"  # type: ignore

    def __init__(self, model: "RobotMission", color: Color):
        """initialize a Radioactivity instance.

        Args:
            model: A model instance
            color: The color of the radioactivity
        """
        super().__init__(model)
        self.color = color

        self.level = 0
        self.instanciate_level()

    def instanciate_level(self):
        if self.color == Color.GREEN:
            self.level = random.uniform(0, 1 / 3)
        elif self.color == Color.YELLOW:
            self.level = random.uniform(1 / 3, 2 / 3)
        elif self.color == Color.RED:
            self.level = random.uniform(2 / 3, 1)


class Waste(mesa.Agent):
    model: "RobotMission"  # type: ignore

    def __init__(self, model: "RobotMission", color: Color):
        """initialize a Waste instance.

        Args:
            model: A model instance
        """
        super().__init__(model)
        self.color = color
