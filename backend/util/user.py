import uuid
from util import chat

class User(object):
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
            chat.to_json()
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

users: list[User] = [
    User("test", "test")
]

users[0].chats.append(chat.Chat())

def match_user(username: str, password: str) -> User | None:
    matching_users: list[User] = [user
                                  for user in users
                                  if user.username == username
                                  and user.password == password]
    if not matching_users:
        return None

    return matching_users[0]

def does_user_already_exist(username: str) -> bool:
    matching_users: list[User] = [user
                                  for user in users
                                  if user.username == username]
    if not matching_users:
        return False

    return True

def create_user(username: str, password: str) -> User | None:
    username_already_used: bool = does_user_already_exist(username)

    if username_already_used:
        return None

    user: User = User(username, password)
    users.append(user)

    return user

def get_user_from_user_id(user_id: str) -> User | None:
    matching_users: list[User] = [user
                                  for user in users
                                  if str(user.user_id) == user_id]
    if not matching_users:
        return None

    return matching_users[0]
