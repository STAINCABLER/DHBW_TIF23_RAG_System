import uuid
from util import chat
from util.clients import postgres_db_client, mongo_db_client
from dataclasses import dataclass, fields, asdict
from datetime import datetime, timezone


@dataclass(kw_only=True)
class User():
    accountId: str
    email: str
    displayName: str
    createdAt: str
    displayNameUpdatedAt: str
    emailUpdatedAt: str
    passwordUpdatedAt: str
    password: str = ""


    def get_chats(self) -> list[chat.Chat]:
        raw_chats: list[dict[str, any]] = []

        with mongo_db_client.create_connection() as client:
            database = client["rag"]
            collection = database["chats"]

            res = collection.find({"accountId": self.accountId})
            for i in res:
                raw_chats.append(i)
        
        chats: list[chat.Chat] = [
            chat.Chat.from_dict(raw_chat)
            for raw_chat in raw_chats
        ]

        return chats

    def get_chat_with_id(self, chat_id: str) -> chat.Chat | None:
        raw_chat: dict[str, any] = {}

        with mongo_db_client.create_connection() as client:
            database = client["rag"]
            collection = database["chats"]

            raw_chat = collection.find_one({"accountId": self.accountId, "chatId": chat_id})
        
        if not raw_chat:
            return None

        return chat.Chat.from_dict(raw_chat)

    def create_chat(self) -> chat.Chat:
        new_chat: chat.Chat = chat.Chat(
            str(uuid.uuid4()),
            "New Chat",
            datetime.now(timezone.utc),
            self.accountId,
            []
            )
        

        with mongo_db_client.create_connection() as client:
            database = client["rag"]
            collection = database["chats"]

            collection.insert_one(asdict(new_chat))



        return new_chat

    @classmethod
    def from_dict(cls, data) -> "User":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        return cls(**filtered_data)
    
    def to_dict(self) -> dict[str, any]:
        return asdict(self)

class UserOld(object):
    users: list["User"] = []
    def __init__(
            self,
            username: str,
            password: str
        ) -> None:
        self.user_id: uuid.UUID = uuid.uuid4()
        self.username: str = username
        self.password: str = password
        self.chats: list[chat.Chat] = []

    def to_dict(self) -> dict[str, str]:
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "password": self.password,
        }

    def get_chats_as_dict(self) -> list[dict[str, any]]:
        return [
            chat.to_dict()
            for chat in self.chats
        ]
    
    def get_raw_chats_as_list(self) -> list[dict[str, any]]:
        return [
            {
                "chat_id": str(chat.chat_id),
                "title": chat.title,
            }
            for chat in self.chats
        ]

    def get_chat_from_chat_id(self, chat_id: str) -> chat.Chat | None:
        matched_chats: list[chat.Chat] = [
            chat
            for chat in self.chats
            if str(chat.chat_id) == chat_id
        ]

        if not matched_chats:
            return None

        return matched_chats[0]

    def create_chat(self) -> chat.Chat:
        new_chat: chat.Chat = chat.Chat()

        self.chats.append(new_chat)
        return new_chat

    def add_entry_to_chat(self, chat_id: str, entry: chat.Entry) -> None:
        ref_chat: chat.Chat = self.get_chat_from_chat_id(chat_id)

        if not ref_chat:
            return
        

        ref_chat.entries.append(entry)

def match_user(username: str, password: str) -> User | None:
    
    # I don't care about SQL-Injection...
    matched_user_data: dict[str, any] = postgres_db_client.fetch_one(
        "SELECT accountId, email, displayName, createdAt, displayNameUpdatedAt, emailUpdatedAt, passwordUpdatedAt "
        "FROM userData "
        f"WHERE email = '{username}' "
        f"AND password = '{password}'"
    )

    if not matched_user_data:
        return None

    return User.from_dict(matched_user_data)

def does_user_already_exist(username: str) -> bool:
    # I don't care about SQL-Injection...
    matched_user_data: dict[str, any] = postgres_db_client.fetch_one(
        "SELECT accountId "
        "FROM userData "
        f"WHERE email = '{username}'"
    )
    if not matched_user_data:
        return False

    return True

def create_user(username: str, password: str) -> User | None:
    username_already_used: bool = does_user_already_exist(username)

    if username_already_used:
        return None

    timestamp_now = datetime.now(timezone.utc)

    user: User = User(
        accountId=str(uuid.uuid4()),
        email=username,
        displayName=username,
        createdAt=timestamp_now,
        displayNameUpdatedAt=timestamp_now,
        emailUpdatedAt=timestamp_now,
        passwordUpdatedAt=timestamp_now,
        password=password
    )

    postgres_db_client.execute(
        "INSERT INTO userData "
        "(accountId, email, displayName, createdAt, displayNameUpdatedAt, emailUpdatedAt, passwordUpdatedAt, password) " \
        "VALUES ("
            f"'{user.accountId}',"
            f"'{user.displayName}',"
            f"'{user.email}',"
            f"TIMESTAMP '{user.createdAt}',"
            f"TIMESTAMP '{user.displayNameUpdatedAt}',"
            f"TIMESTAMP '{user.emailUpdatedAt}',"
            f"TIMESTAMP '{user.passwordUpdatedAt}',"
            f"'{user.password}'"
        ") "
    )


    return user

def get_user_from_user_id(user_id: str) -> User | None:
    matched_user_data: dict[str, any] = postgres_db_client.fetch_one(
        "SELECT accountId, email, displayName, createdAt, displayNameUpdatedAt, emailUpdatedAt, passwordUpdatedAt "
        "FROM userData "
        f"WHERE accountId = '{user_id}' "
    )

    if not matched_user_data:
        return None

    return User.from_dict(matched_user_data)


#create_user("test", "test")
