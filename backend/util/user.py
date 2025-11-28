import dataclasses
import datetime
import hashlib
import typing

import database.postgres

@dataclasses.dataclass
class User(object):
    id: int
    username: str
    email: str
    password_hash: str
    profile_type: typing.Literal["student", "professional", "researcher"]
    created_at: datetime.datetime
    last_login: datetime.datetime
    is_active: bool
    preferences: dict[str, str] | None = None

    def update_last_login_to_now(self) -> None:
        self.last_login = datetime.datetime.now()
        database.postgres.execute(
            "UPDATE users "
            "SET "
                f"last_login='{self.last_login}' "
            "WHERE "
                f"id = {self.id}"
        )

    def update_user(self) -> None:
        database.postgres.execute(
            "UPDATE users "
            "SET "
                f"username='{self.username}', "
                f"email='{self.email}', "
                f"password_hash='{self.password_hash}', "
                f"profile_type='{self.profile_type}', "
                f"last_login='{self.last_login}', "
                f"is_active={self.is_active} "
            "WHERE "
                f"id = {self.id}"
        )

    @staticmethod
    def create_user(username: str, email: str, password: str, profile_type: str = "student") -> "User":
        result = database.postgres.fetch_one(
            "SELECT id "
            "FROM users "
                "WHERE "
                    f"username = '{username}' "
                    f"OR email = '{email}'"
        )
        if result:
            return None
        password_hash: str = hashlib.sha256(password.encode()).hexdigest()
        database.postgres.execute(
            "INSERT INTO users ("
                "username,"
                "email,"
                "password_hash,"
                "profile_type"
            ") "
            "VALUES ( "
                f"'{username}', "
                f"'{email}', "
                f"'{password_hash}', "
                f"'{profile_type}'"
            ")"
        )

        return User.find_user_by_email_and_password_hash(email, password_hash)

    @staticmethod
    def get_all_users() -> list["User"]:
        result: list[dict[str, any]] = database.postgres.fetch_all(
            "SELECT "
                "id, username, email, password_hash, profile_type, created_at, last_login, is_active, preferences "
            "FROM users"
        )

        return [
            User.from_dict(user)
            for user in result
        ]

    @staticmethod
    def find_user_by_id(user_id: int) -> "User":

        result: dict[str, any] | None = database.postgres.fetch_one(
            "SELECT "
                "id, username, email, password_hash, profile_type, created_at, last_login, is_active, preferences "
            "FROM users "
            "WHERE "
                f"id = {user_id}"
        )

        if not result:
            return None

        return User.from_dict(result)

    @staticmethod
    def find_user_by_email_and_password_hash(email: str, password_hash: str) -> "User":

        result: dict[str, any] | None = database.postgres.fetch_one(
            "SELECT "
                "id, username, email, password_hash, profile_type, created_at, last_login, is_active "
            "FROM users "
            "WHERE "
                f"email = '{email}' "
                f"AND password_hash = '{password_hash}' "
                "AND is_active"
        )

        if not result:
            return None

        return User.from_dict(result)

    @classmethod
    def from_dict(cls, data) -> "User":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in dataclasses.fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        return cls(**filtered_data)

    def to_dict(self) -> dict[str, any]:
        return dataclasses.asdict(self)

    def to_spare_dict(self) -> dict[str, any]:
        user_data: dict[str, any] = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "profile_type": self.profile_type,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }

        if self.last_login:
            user_data["last_login"] = self.last_login.isoformat()


        return user_data
