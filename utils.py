"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from enum import IntEnum
import random


Position = tuple[int, int]


class Color(IntEnum):
    GREEN = 1
    YELLOW = 2
    RED = 3

    def to_hex(self) -> str:
        return {Color.GREEN: "#2dbd3e", Color.YELLOW: "#dee038", Color.RED: "#e34d12"}[self]

    def to_light_hex(self) -> str:
        return {Color.GREEN: "#e4fade", Color.YELLOW: "#f5f3c9", Color.RED: "#fadede"}[self]


class Direction(IntEnum):
    UP = 1
    DOWN = 2
    RIGHT = 3
    LEFT = 4

    @staticmethod
    def random() -> "Direction":
        return random.choice(list(Direction))

    def to_coords(self) -> Position:
        if self == Direction.UP:
            return 0, 1
        elif self == Direction.DOWN:
            return 0, -1
        elif self == Direction.RIGHT:
            return 1, 0
        elif self == Direction.LEFT:
            return -1, 0
        raise ValueError("Invalid direction")
