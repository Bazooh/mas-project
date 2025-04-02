from abc import ABC
from communication import Message

class Information(ABC):
    def __init__(self, message: Message) -> None:
        self.message = message

    def to_bytes(self) -> bytes:
        return bytes()
    
    def from_bytes(self, bytes: bytes) -> None: