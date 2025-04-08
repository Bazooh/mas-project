from abc import ABC
from communication import Message, Mailbox, ContentType, message_to_readable_data


class Information(ABC):
    def __init__(self) -> None:
        pass

    def update(self, mailbox: Mailbox, keep_unread) -> None:
        pass


class CombinedInformation(Information):
    def __init__(self, informations: dict[str, Information]) -> None:
        self.informations = informations

    def update(self, mailbox: Mailbox, keep_unread=False) -> None:
        for information in self.informations.values():
            information.update(mailbox, keep_unread=True)
        mailbox.read_all_unread(keep_unread=keep_unread)


class AllPositionsAndColorsInformation(Information):
    def __init__(self) -> None:
        self.positions = {}
        self.colors = {}

    def update_from_message(self, message: Message) -> None:
        unique_id, position, color = message_to_readable_data(message)
        self.positions[unique_id] = position
        self.colors[unique_id] = color

    def update(self, mailbox: Mailbox, keep_unread=False) -> None:
        new_messages = mailbox.read_all_unread(keep_unread=keep_unread)
        for message in new_messages:
            if message.get_type() == ContentType.ID_POSITION_COLOR:
                self.update_from_message(message)


class TargetInformation(Information):
    """
    self.targets is a list of tuples (x, y) where x and y are the coordinates of the target. Top priority is self.targets[0].
    """

    def __init__(self) -> None:
        super().__init__()
        self.targets = []

    def update(self, mailbox: Mailbox, keep_unread=False) -> None:
        new_messages = mailbox.read_all_unread(keep_unread=keep_unread)
        for message in new_messages:
            if message.get_type() == ContentType.TARGET:
                self.targets.append(message_to_readable_data(message))
