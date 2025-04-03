"""
Group: 14
Members: Aymeric Conti, Pierre Jourdin
Date: 11/03/2025
"""

import random
import mesa

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator, cast

from action import Action
from knowledge import ChickenKnowledge
from objects import Waste
from utils import Color, Position

from communication import Mailbox, Message, ContentType, readable_data_to_message
from information import AllPositionsInformation

if TYPE_CHECKING:
    from model import RobotMission
    from perception import Perception


class Inventory:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.wastes: list[Waste] = []

    def is_full(self) -> bool:
        return len(self.wastes) >= self.capacity

    def is_empty(self) -> bool:
        return len(self.wastes) == 0

    def get_highest_waste(self) -> Waste | None:
        if self.is_empty():
            return None
        return max(self.wastes, key=lambda waste: waste.color)

    def add(self, waste: Waste) -> None:
        self.wastes.append(waste)

    def remove(self, waste: Waste) -> None:
        self.wastes.remove(waste)

    def clear(self) -> None:
        self.wastes.clear()

    def random(self) -> Waste:
        return random.choice(self.wastes)

    def __contains__(self, waste: Waste) -> bool:
        return waste in self.wastes

    def __iter__(self) -> Iterator[Waste]:
        return iter(self.wastes)

    def __len__(self) -> int:
        return len(self.wastes)


class Agent(mesa.Agent, ABC):
    model: "RobotMission"  # type: ignore

    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model)
        self.knowledge = ChickenKnowledge()
        self.perception: Perception
        self.color = color
        self.inventory_capacity = 1 if color == Color.RED else 2
        self.inventory = Inventory(self.inventory_capacity)

    def init_perception(self, perception: "Perception") -> None:
        self.perception = perception

    def get_true_pos(self) -> Position:
        assert self.pos is not None, "Trying to get the position of an agent that is not placed"
        return cast(Position, self.pos)

    def step(self) -> None:
        self.knowledge.update(self.perception)
        self.action = self.deliberate()
        self.perception = self.model.do(self.action, self)

    @abstractmethod
    def deliberate(self) -> Action: ...


class RandomAgent(Agent):
    def deliberate(self) -> Action:
        return Action.random_from_agent(self)
    
class CommunicationAgent(Agent):
    def __init__(self, model: "RobotMission", color: Color) -> None:
        super().__init__(model, color)
        self.mailbox = Mailbox()
        self.information = AllPositionsInformation()

    def send_messages(self) -> None:
        content_type = ContentType.ID_POSITION
        readable_data = [self.unique_id, self.get_true_pos()]
        message = readable_data_to_message(readable_data, content_type)
        self.model.message_service.send_all(self.model.get_agents(), message)

    def step(self) -> None:
        self.knowledge.update(self.perception)
        self.information.update(self.mailbox)
        self.action = self.deliberate()
        self.send_messages()
        self.perception = self.model.do(self.action, self)


GreenAgent = RandomAgent
YellowAgent = RandomAgent
RedAgent = RandomAgent
