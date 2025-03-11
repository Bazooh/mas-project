"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from enum import Enum
import random


Position = tuple[int, int]


class Color(Enum):
    GREEN = 1
    YELLOW = 2
    RED = 3


class Direction(Enum):
    UP = 1
    DOWN = 2
    RIGHT = 3
    LEFT = 4

    @staticmethod
    def random() -> "Direction":
        return random.choice(list(Direction))

    def to_coords(self) -> Position:
        if self == Direction.UP:
            return (0, 1)
        elif self == Direction.DOWN:
            return (0, -1)
        elif self == Direction.RIGHT:
            return (1, 0)
        elif self == Direction.LEFT:
            return (-1, 0)
        raise ValueError("Invalid direction")
