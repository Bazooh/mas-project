from __future__ import annotations

from enum import Enum
from agent import Agent

content_type_to_class: dict[ContentType, type] = {}

class ContentType(Enum):
    MAP = 0

    def to_class(self) -> type:
        return content_type_to_class[self]

class Message:
    """
    The object we transfer between agents.
    """
    def __init__(self, content : bytes, content_type : ContentType) -> None:
        self.content = content # content in bytes
        self.type = content_type # type of content

    def get_type(self) -> ContentType:
        return self.type

    def get_content(self) -> bytes:
        return self.content

class Mailbox:
    """
    The mailbox of the agent : the agent receives messages through it.
    """
    def __init__(self):
        self.read_messages: list[Message] = [] # most recent is at the end
        self.unread_messages: list[Message] = [] # most recent is at the end

    def receive(self, message):
        self.unread_messages.append(message)

    def read_latest_unread(self) -> Message:
        new_message = self.unread_messages.pop(0)
        self.read_messages.append(new_message)
        return new_message
    
    def read_all_unread(self) -> list[Message]:
        res = []
        while len(self.unread_messages) > 0:
            new_message = self.read_latest_unread()
            res.append(new_message)
        return res
    
class MessageService:
    """
    Object possessed by the model that can transfer messages between agents.
    """
    def __init__(self):
        pass

    def send(self, receiver: Agent, message: Message):
        receiver.mailbox.receive(message)

    def send_all(self, receivers: list[Agent], message: Message):
        for receiver in receivers:
            self.send(receiver, message)