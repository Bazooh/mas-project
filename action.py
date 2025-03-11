from abc import ABC, abstractmethod


class Action(ABC):
    @abstractmethod
    def apply(self) -> None: ...


class Move(Action):
    def apply(self) -> None: ...

    @classmethod
    def random(cls) -> "Action":
        return cls()
