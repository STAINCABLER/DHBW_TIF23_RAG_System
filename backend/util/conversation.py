import dataclasses
import datetime
import typing
import uuid
import werkzeug.utils

import database.postgres
import util.file


@dataclasses.dataclass()
class ConversationMessage(object):
    message_id: int
    conversation_id: int
    role: typing.Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime.datetime
    metadata: dict[str, any]

    @staticmethod
    def get_conversation_message_from_message_id(message_id: int) -> "ConversationMessage":
        raw_conversation_message: dict[str, any]= database.postgres.fetch_one(
            "SELECT * "
            "FROM messages "
            f"WHERE message_id = {message_id}"
        )

        if not raw_conversation_message:
            return None

        converted_conversation_message: ConversationMessage =  ConversationMessage.from_dict(raw_conversation_message)

        return converted_conversation_message


    @classmethod
    def from_dict(cls, data) -> "ConversationMessage":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in dataclasses.fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        for field in dataclasses.fields(cls):
            if field.name.lower() not in filtered_data:
                filtered_data[field.name.lower()] = None
        return cls(**filtered_data)

    def to_dict(self) -> dict[str, any]:
        raw_dict: dict[str, any] = dataclasses.asdict(self)

        raw_dict["timestamp"] = self.timestamp.isoformat()

        return raw_dict


@dataclasses.dataclass()
class Conversation(object):
    conversation_id: int
    user_id: int
    title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_active: bool
    messages: list[ConversationMessage]

    def update_updated_at_to_now(self) -> None:
        self.updated_at = datetime.datetime.now()
        database.postgres.execute(
            "UPDATE conversations "
            "SET "
                f"updated_at='{self.updated_at}' "
            "WHERE "
                f"conversation_id = {self.conversation_id}"
        )

    def load_all_messages(self) -> None:
        result: list[dict[str, any]] = database.postgres.fetch_all(
            "SELECT * "
            "FROM messages "
            f"WHERE conversation_id = {self.conversation_id}"
        )

        self.messages = [
            ConversationMessage.from_dict(raw_message)
            for raw_message in result
        ]
    
    def get_all_uploaded_files(self) -> list[util.file.UploadedFile]:
        result: list[dict[str, any]] = database.postgres.fetch_all(
            "SELECT * "
            "FROM uploaded_files "
            f"WHERE conversation_id = {self.conversation_id}"
        )

        return [
            util.file.UploadedFile.from_dict(raw_message)
            for raw_message in result
        ]
    
    def create_uploaded_file(self, file_name: str, file_type: str) -> util.file.UploadedFile | None:
        file_uuid: uuid.UUID = uuid.uuid4()
        escaped_file_name: str = file_name.replace("'", "\\'")
        database.postgres.execute(
            "INSERT INTO uploaded_files ("
                "conversation_id, original_filename, file_uuid, file_type "
            ")"
            "VALUES ("
                f"{self.conversation_id},"
                f"'{escaped_file_name}',"
                f"'{file_uuid}',"
                f"'{file_type}'"
            ")"
        )

        result: dict[str, any] = database.postgres.fetch_one(
            "SELECT MAX(file_id) FROM uploaded_files "
            f"WHERE conversation_id = {self.conversation_id}"
        )

        if not result:
            return None
        
        file_id: int = result["max"]


        return util.file.UploadedFile.find_by_file_id(file_id)

    def create_conversation_message(self, content: str, role: str, metadata: dict[str, any] = None) -> ConversationMessage | None:
        if metadata is None:
            metadata = {}
        database.postgres.execute(
            "INSERT INTO messages ("
                "conversation_id, role, content, metadata"
            ")"
            "VALUES ("
                f"{self.conversation_id},"
                f"'{role}',"
                f"'{content}',"
                f"'{metadata}'"
            ")"
        )

        self.update_updated_at_to_now()

        result: dict[str, any] = database.postgres.fetch_one(
            "SELECT MAX(message_id) FROM messages "
            f"WHERE conversation_id = {self.conversation_id}"
        )

        if not result:
            return None
        
        message_id: int = result["max"]
        
        return ConversationMessage.get_conversation_message_from_message_id(message_id)

    @staticmethod
    def get_all_conversations_from_user_id(user_id: int) -> list["Conversation"]:
        raw_conversations: list[dict[str, any]] = database.postgres.fetch_all(
            "SELECT * "
            "FROM conversations "
            f"WHERE user_id = {user_id}"
        )

        converted_conversations: list[Conversation] = [
            Conversation.from_dict(raw_conversation)
            for raw_conversation in raw_conversations
        ]

        return converted_conversations

    @staticmethod
    def get_conversation_from_conversation_id(conversation_id: int) -> "Conversation":
        raw_conversation: dict[str, any]= database.postgres.fetch_one(
            "SELECT * "
            "FROM conversations "
            f"WHERE conversation_id = {conversation_id}"
        )

        if not raw_conversation:
            return None

        converted_conversation: Conversation =  Conversation.from_dict(raw_conversation)

        return converted_conversation

    @staticmethod
    def create_conversation_from_user(user_id: int, title: str = "Placeholder") -> "Conversation":
        database.postgres.execute(
            "INSERT INTO conversations ("
                "user_id, title"
            ") "
            "VALUES ("
                f"{user_id},"
                f"'{title}'"
            ")"
        )

        result: dict[str, any] = database.postgres.fetch_one(
            "SELECT MAX(conversation_id) FROM conversations"
        )

        if not result:
            return None

        conversation_id: int = result["max"]

        return Conversation.get_conversation_from_conversation_id(conversation_id)

    
    @classmethod
    def from_dict(cls, data) -> "Conversation":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in dataclasses.fields(cls)
            if f.name.lower() in data
            or f.name in data
        }

        for field in dataclasses.fields(cls):
            if field.name.lower() not in filtered_data:
                filtered_data[field.name.lower()] = None
        return cls(**filtered_data)

    def to_reduced_dict(self) -> dict[str, any]:
        full_dict: dict[str, any] = self.to_full_dict()
        del full_dict["messages"]

        return full_dict

    def to_full_dict(self) -> dict[str, any]:
        raw_dict: dict[str, any] = dataclasses.asdict(self)

        raw_dict["created_at"] = self.created_at.isoformat()
        raw_dict["updated_at"] = self.updated_at.isoformat()

        if self.messages:
            raw_dict["messages"] = [
                message.to_dict()
                for message in self.messages
            ]

        return raw_dict
