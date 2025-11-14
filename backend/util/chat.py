from dataclasses import dataclass
import uuid

@dataclass
class Entry():
    question: str
    response: str


    def to_json(self) -> dict[str, any]:
        return {
            "question": self.question,
            "response": self.response,
        }

class Chat():
    def __init__(self) -> None:
        self.chat_id: uuid.UUID = uuid.uuid4()
        self.title: str = ""
        self.entries: list[Entry] = []

    def to_json(self) -> dict[str, any]:
        return {
            "chat_id": str(self.chat_id),
            "title": self.title,
            "entries": [entry.to_json()
                        for entry in self.entries],
        }
