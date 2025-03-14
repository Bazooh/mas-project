"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from action import Merge, Move, Pick, Drop
from objects import Waste
from utils import Color, Direction

if TYPE_CHECKING:
    from agent import Inventory
    from perception import Perception


class Knowledge(ABC):
    @abstractmethod
    def update(self, perception: Perception) -> None: ...

    @abstractmethod
    def copy(self) -> Knowledge: ...

    def try_merge(self) -> Merge | None:
        return None

    def try_move(self, direction: Direction) -> Move | None:
        return None

    def try_pick(self) -> Pick | None:
        return None

    def try_drop(self, waste: Waste) -> Drop | None:
        return None

    def __add__(self, other: Knowledge) -> Knowledge:
        return MultipleKnowledges(self, other)


class MultipleKnowledges(Knowledge):
    def __init__(self, knowledge1: Knowledge, knowledge2: Knowledge) -> None:
        self.knowledge1 = knowledge1
        self.knowledge2 = knowledge2

    def update(self, perception: Perception) -> None:
        self.knowledge1.update(perception)
        self.knowledge2.update(perception)

    def try_merge(self) -> Merge | None:
        merge = self.knowledge1.try_merge()
        if merge is not None:
            return merge
        return self.knowledge2.try_merge()

    def try_move(self, direction: Direction) -> Move | None:
        move = self.knowledge1.try_move(direction)
        if move is not None:
            return move
        return self.knowledge2.try_move(direction)

    def try_pick(self) -> Pick | None:
        pick = self.knowledge1.try_pick()
        if pick is not None:
            return pick
        return self.knowledge2.try_pick()

    def try_drop(self, waste: Waste) -> Drop | None:
        drop = self.knowledge1.try_drop(waste)
        if drop is not None:
            return drop
        return self.knowledge2.try_drop(waste)

    def copy(self) -> MultipleKnowledges:
        return MultipleKnowledges(self.knowledge1.copy(), self.knowledge2.copy())


class History(Knowledge):
    def __init__(self, knowledge: Knowledge) -> None:
        self.knowledge = knowledge
        self.history: list[Knowledge] = []

    def update(self, perception: Perception) -> None:
        new_knowledge = self.knowledge.copy()
        new_knowledge.update(perception)
        self.history.append(new_knowledge)

    def copy(self) -> History:
        history = History(self.knowledge.copy())
        for knowledge in self.history:
            history.history.append(knowledge.copy())
        return history


class PositionKnowledge(Knowledge):
    def __init__(self) -> None:
        self.x: int
        self.y: int

    def update(self, perception: Perception) -> None: ...

    def copy(self) -> PositionKnowledge:
        new_pos = PositionKnowledge()
        new_pos.x = self.x
        new_pos.y = self.y
        return new_pos


class AllKnowledge(Knowledge):
    def __init__(self) -> None:
        self.perception: Perception
        self.inventory: Inventory
        self.color: Color

    def update(self, perception: Perception) -> None:
        self.perception = perception
        self.inventory = perception.inventory
        self.color = perception.color

    def try_merge(self) -> Merge | None:
        mergeable_waste = [waste for waste in self.inventory if waste.color == self.color]
        if len(mergeable_waste) < 2:
            return None

        return Merge(mergeable_waste[0], mergeable_waste[1])

    def try_move(self, direction: Direction) -> Move | None:
        if direction not in self.perception:
            return None

        case = self.perception[direction]
        if case.agent is not None or case.color > self.color:
            return None

        return Move(direction)

    def try_drop(self, waste: Waste) -> Drop | None:
        if waste not in self.inventory:
            return None

        if self.perception[Direction.NONE].waste is not None:
            return None

        return Drop(waste)

    def try_pick(self) -> Pick | None:
        if self.inventory.is_full():
            return None

        case = self.perception[Direction.NONE]
        if case.waste is None:
            return None

        if case.waste.color != self.color:
            return None

        return Pick()

    def copy(self) -> AllKnowledge:
        new_knowledge = AllKnowledge()
        new_knowledge.perception = self.perception
        return new_knowledge
