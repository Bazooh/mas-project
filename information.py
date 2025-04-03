from abc import ABC
from communication import Message, Mailbox, ContentType, message_to_readable_data

class Information(ABC):
    def __init__(self) -> None:
        pass

class AllPositionsInformation(Information):
    def __init__(self) -> None:
        self.positions = {}

    def update_from_message(self, message: Message) -> None:
        content = message.get_content()
        readable_data = message_to_readable_data(message)
        unique_id, position = readable_data[0], readable_data[1]
        self.positions[unique_id] = position

    def update(self, mailbox: Mailbox) -> None:
        new_messages = mailbox.read_all_unread()
        for message in new_messages:
            if message.get_type() == ContentType.ID_POSITION:
                self.update_from_message(message)