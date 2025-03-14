"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

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

    def to_rgb(self) -> tuple[float, float, float]:
        hex = self.to_hex()
        return int(hex[1:3], 16) / 255, int(hex[3:5], 16) / 255, int(hex[5:7], 16) / 255

    def to_light_rgb(self) -> tuple[float, float, float]:
        hex = self.to_light_hex()
        return int(hex[1:3], 16) / 255, int(hex[3:5], 16) / 255, int(hex[5:7], 16) / 255


class Direction(IntEnum):
    NONE = 0
    UP = 1
    DOWN = 2
    RIGHT = 3
    LEFT = 4

    @staticmethod
    def random(exclude: set[Direction] = set()) -> Direction:
        return random.choice(list(set(Direction.not_none()) - exclude))

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

    @staticmethod
    def get_direction(pos1: Position, pos2: Position) -> Direction:
        if pos1[0] < pos2[0]:
            return Direction.RIGHT
        if pos1[0] > pos2[0]:
            return Direction.LEFT
        if pos1[1] < pos2[1]:
            return Direction.UP
        if pos1[1] > pos2[1]:
            return Direction.DOWN
        return Direction.NONE

    @staticmethod
    def not_none() -> list[Direction]:
        return [direction for direction in Direction if direction != Direction.NONE]
