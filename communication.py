from __future__ import annotations

from enum import Enum
import pickle

content_type_to_class: dict[ContentType, type] = {}

class ContentType(Enum):
    MAP = 0
    ID_POSITION = 1
    ID_POSITION_COLOR = 2
    TARGET = 3

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
    
def readable_data_to_message(raw_data, content_type : ContentType) -> Message:
    return Message(pickle.dumps(raw_data), content_type)

def message_to_readable_data(message : Message) :
    return pickle.loads(message.get_content())

class Mailbox:
    """
    The mailbox of the agent : the agent receives messages through it.
    """
    def __init__(self):
        self.read_messages: list[Message] = [] # most recent is at the end
        self.unread_messages: list[Message] = [] # most recent is at the end

    def receive(self, message) -> None:
        self.unread_messages.append(message)

    def read_latest_unread(self, keep_unread = False) -> Message:
        new_message = self.unread_messages.pop(0)
        self.read_messages.append(new_message)
        return new_message
    
    def read_all_unread(self, keep_unread = False) -> list[Message]:
        res = []
        while len(self.unread_messages) > 0:
            new_message = self.read_latest_unread()
            res.append(new_message)
        res.reverse() 
        if keep_unread:
            self.unread_messages = self.unread_messages + res
        return res # most recent is at the end