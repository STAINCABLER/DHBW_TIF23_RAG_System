import util
from access import redis

class RedisTester(util.BaseTester):
    def __init__(self):
        super().__init__()
        self.db_name: str = "Redis"

    def setup(self) -> None:
        with redis.open_session() as session:
            session.hset("user:1", mapping={"name": "host", "email": "hostinger"})


    def test_read(self, number_of_operations: int = 100) -> float:
        print("Read Test")
        redis_timer: util.Timer = util.Timer()
        redis_timer.start()
        for i in range(number_of_operations):
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            with redis.open_session() as session:
                session.hgetall("user:1")

        redis_timer.stop()
        print("")

        return redis_timer.duration

    def test_write(self, number_of_operations: int = 100) -> float:
        print("Write Test")
        redis_timer: util.Timer = util.Timer()
        redis_timer.start()
        for i in range(number_of_operations):
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            with redis.open_session() as session:
                session.hset(f"user:{i+2}", mapping={"name": f"host{i}", "email": f"hostinger{i}"})

        redis_timer.stop()
        print("")

        return redis_timer.duration



    def test_update(self, number_of_operations: int = 100) -> float:
        print("Update Test")
        redis_timer: util.Timer = util.Timer()
        redis_timer.start()
        for i in range(number_of_operations):
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            with redis.open_session() as session:
                session.hset(f"user:1", mapping={"name": f"host{i}", "email": "hostinger"})

        redis_timer.stop()
        print("")

        return redis_timer.duration

