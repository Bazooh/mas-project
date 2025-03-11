from enum import Enum
import random


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
