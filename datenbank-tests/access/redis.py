import contextlib
import os
import redis

REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")


@contextlib.contextmanager
def open_session():
    redis_session: redis.Redis = redis.Redis(REDIS_HOST)
    yield redis_session
    redis_session.close()

