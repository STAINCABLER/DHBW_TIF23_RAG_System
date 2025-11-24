from dataclasses import dataclass, field, fields, asdict
import uuid
import enum
from util.clients import mongo_db_client


@dataclass
class ChatMessage():
    role: str
    text: str
    files: list

    @classmethod
    def from_dict(cls, data) -> "ChatMessage":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        return cls(**filtered_data)
    
    def to_dict(self) -> dict[str, any]:
        return asdict(self)

@dataclass
class Chat():
    chatId: str
    chatTitle: str
    createdAt: str
    accountId: str
    messages: list[ChatMessage]

    def to_chat_overview(self) -> dict[str, any]:
        return {
            "chatId": self.chatId,
            "chatTitle": self.chatTitle
        }


    def update_messages(self) -> None:
        with mongo_db_client.create_connection() as client:
            database = client["rag"]
            collection = database["chats"]

            collection.update_one(
                {"accountId": self.accountId, "chatId": self.chatId},
                {"$set": {
                    "messages": [message.to_dict()
                                 for message in self.messages]
                }}
            )

    @classmethod
    def from_dict(cls, data) -> "Chat":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        if "messages" in filtered_data:
            new_messages: list[ChatMessage] = [ChatMessage.from_dict(message)
                                               for message in filtered_data["messages"]]
            filtered_data["messages"] = new_messages
        return cls(**filtered_data)
    
    def to_dict(self) -> dict[str, any]:
        return asdict(self)



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

class ChatOld():
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
