from dataclasses import dataclass, field
import uuid
import enum

class EntryRole(enum.Enum):
    USER = ("user")
    ASSISTENT = ("assistent")

    def __init__(self, role_name: str):
        super().__init__()
        self.role_name: str = role_name


@dataclass
class Entry():
    role: EntryRole
    text: str
    files: list = field(default_factory=list)


    def to_dict(self) -> dict[str, any]:
        return {
            "type": self.role.role_name,
            "text": self.text,
            "files": str(self.files)
        }

class Chat():
    def __init__(self) -> None:
        self.chat_id: uuid.UUID = uuid.uuid4()
        self.title: str = ""
        self.entries: list[Entry] = []

    def to_dict(self) -> dict[str, any]:
        return {
            "chat_id": str(self.chat_id),
            "title": self.title,
            "entries": [entry.to_dict()
                        for entry in self.entries],
        }
