import dataclasses
import datetime
import flask
import functools
import uuid

import database.redis
import util.user


SESSION_DURATION: int = 10 * 60

@dataclasses.dataclass()
class SessionToken(object):
    session_id: uuid.UUID
    user_id: int
    created_at: datetime.datetime
    expires_at: datetime.datetime

    def revoke_session_token(self) -> None:
        with database.redis.open_session() as redis_session:
            session_name: str = f"session:{str(self.session_id)}"

            raw_session_data = redis_session.hgetall(session_name)
            if raw_session_data:
                redis_session.delete(session_name)

    def get_user(self) -> util.user.User | None:
        return util.user.User.find_user_by_id(self.user_id)

    @staticmethod
    def load_from_session_id(session_id: uuid.UUID) -> "SessionToken":

        expires_at: datetime.datetime = datetime.datetime.now() + datetime.timedelta(1)

        raw_session_data: dict[bytes, bytes] = {}

        with database.redis.open_session() as redis_session:
            session_name: str = f"session:{str(session_id)}"
            raw_session_data = redis_session.hgetall(session_name)

            if not raw_session_data:
                return None

            redis_session.expire(session_name, SESSION_DURATION)
            redis_session.hset(session_name, "expires_at", expires_at.timestamp())

        session_data: dict[str, str] = {
            key.decode("utf-8"): value.decode("utf-8")
            for key, value in raw_session_data.items()
        }

        created_at: datetime.datetime = datetime.datetime.fromtimestamp(float(session_data["created_at"]))

        session_id: uuid.UUID = uuid.UUID(session_data["session_id"])
        user_id: int = int(session_data["user_id"])

        session_token: SessionToken = SessionToken(session_id, user_id, created_at, expires_at)


        return session_token


    @staticmethod
    def create_session_token(user_id: int) -> "SessionToken":
        session_token: SessionToken = SessionToken(
            uuid.uuid4(),
            user_id,
            datetime.datetime.now(),
            datetime.datetime.now() + datetime.timedelta(days=1)
        )

        with database.redis.open_session() as redis_session:
            session_name: str = f"session:{str(session_token.session_id)}"
            redis_session.hset(name=session_name, mapping=session_token.to_dict())
            redis_session.expire(session_name, SESSION_DURATION)

        return session_token


    def to_dict(self) -> dict[str, any]:
        raw_dict: dict[str, any] = dataclasses.asdict(self)
        raw_dict["session_id"] = str(raw_dict["session_id"])
        raw_dict["created_at"] = self.created_at.timestamp()
        raw_dict["expires_at"] = self.expires_at.timestamp()

        return raw_dict
    
    @staticmethod
    def get_current_session_token() -> "SessionToken":
         # Flask Session Option
            raw_session_id: str = flask.session.get("session_id", None)
            if not raw_session_id:
                return None

            # Cookie Option
            # raw_session_id: str = flask.request.cookies.get("SESSION_ID", None)
            # if not raw_session_id:
            #     return None

            session_id: uuid.UUID = uuid.UUID(raw_session_id)


            session_token: SessionToken = SessionToken.load_from_session_id(session_id)
            return session_token


def requires_session(add_session_token: bool = False):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwds):
            session_token: SessionToken = SessionToken.get_current_session_token()

            if not session_token:
                flask.session.clear()
                return flask.Response(
                    None,
                    401,
                    {
                        "Set-Cookie": "SESSION_ID=deleted; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT"
                    }
                )
            if add_session_token:
                kwds["session_token"] = session_token

            return function(*args, **kwds)
        return wrapper
    return decorator