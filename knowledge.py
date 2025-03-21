"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

from __future__ import annotations

import torch

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from action import Merge, Move, Pick, Drop
from objects import Waste
from utils import Color, Direction, Position

if TYPE_CHECKING:
    from agent import Inventory
    from perception import Perception


class Knowledge(ABC):
    @abstractmethod
    def update(self, perception: Perception) -> None: ...

    @abstractmethod
    def to_tensor(self) -> torch.Tensor: ...

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


class ChickenKnowledge(Knowledge):
    """Not very knowledgeable, just a chicken."""

    def update(self, perception: Perception) -> None:
        pass

    def to_tensor(self) -> torch.Tensor:
        return torch.empty()


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

    def to_tensor(self) -> torch.Tensor:
        return torch.cat((self.knowledge1.to_tensor(), self.knowledge2.to_tensor()))


T = TypeVar("T", bound=Knowledge)


class History(Knowledge, Generic[T]):
    def __init__(self, knowledge_type: type[T]) -> None:
        self.knowledge_type = knowledge_type
        self.history: list[T] = []

    def update(self, perception: Perception) -> None:
        new_knowledge = self.knowledge_type()
        new_knowledge.update(perception)
        self.history.append(new_knowledge)

    def try_merge(self) -> Merge | None:
        return self.history[-1].try_merge()

    def try_move(self, direction: Direction) -> Move | None:
        return self.history[-1].try_move(direction)

    def try_pick(self) -> Pick | None:
        return self.history[-1].try_pick()

    def try_drop(self, waste: Waste) -> Drop | None:
        return self.history[-1].try_drop(waste)

    def to_tensor(self) -> torch.Tensor:
        return self.history[-1].to_tensor()


class AllKnowledge(Knowledge):
    def __init__(self) -> None:
        self.perception: Perception
        self.inventory: Inventory
        self.color: Color
        self.dump_pos: Position
        self.step = 0

    def update(self, perception: Perception) -> None:
        self.perception = perception
        self.inventory = perception.inventory
        self.color = perception.color
        self.dump_pos = perception.dump_pos
        self.step += 1

    @property
    def pos(self) -> Position:
        me = self.perception[Direction.NONE].agent
        assert me is not None, "Trying to get the position of an agent that is not placed"
        return me.get_true_pos()

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

    def look_around(self) -> Move | None:
        for direction in self.perception:
            if direction == Direction.NONE:
                continue
            waste = self.perception[direction].waste
            if waste is not None and waste.color == self.color:
                return Move(direction)
        return None

    def to_tensor(self) -> torch.Tensor:
        """
        Returns a tensor of shape (25,) with the following values :
        - Step / 100
        - Number of wastes of my color in my inventory
        - Number of wastes of the next color in my inventory
        - Is there a waste on me
        - Is there a waste of my color on me

        for each direction:
            - Can I move in this direction (does not take into account if there is an agent in this direction)
            - Is there a waste in this direction
            - Is there a waste of my color in this direction
            - Is there an agent in this direction
            - Is there an agent of my color in this direction
        """
        tensor = torch.zeros(24)
        for waste in self.inventory:
            tensor[waste.color - self.color] += 1

        waste = self.perception[Direction.NONE].waste
        tensor[2] = waste is not None
        tensor[3] = waste is not None and waste.color == self.color

        for i, direction in enumerate(Direction.not_none()):
            if direction not in self.perception:
                continue

            case = self.perception[direction]
            tensor[i * 5 + 4] = case.color <= self.color
            tensor[i * 5 + 5] = case.waste is not None
            tensor[i * 5 + 6] = case.waste is not None and case.waste.color == self.color
            tensor[i * 5 + 7] = case.agent is not None
            tensor[i * 5 + 8] = case.agent is not None and case.agent.color == self.color

        return tensor
