"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from perception import Perception


class Knowledge(ABC):
    @abstractmethod
    def update(self, perception: Perception) -> None: ...

    @abstractmethod
    def copy(self) -> Knowledge: ...

    def __add__(self, other: Knowledge) -> Knowledge:
        return MultipleKnowledges(self, other)


class MultipleKnowledges(Knowledge):
    def __init__(self, knowledge1: Knowledge, knowledge2: Knowledge) -> None:
        self.knowledge1 = knowledge1
        self.knowledge2 = knowledge2

    def update(self, perception: Perception) -> None:
        self.knowledge1.update(perception)
        self.knowledge2.update(perception)

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
