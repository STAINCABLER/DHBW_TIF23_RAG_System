import time
from access import mongo, postgres, redis


class Timer():
    def __init__(self):
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration: float = 0.0
    
    def start(self) -> None:
        self.start_time = time.perf_counter()
    
    def stop(self) -> None:
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
    

def setup() -> None:
    with postgres.create_connection("rag") as connection:
        cursor = connection.cursor()

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS PerfTest ("
                "id SERIAL PRIMARY KEY,"
                "name TEXT,"
                "email TEXT UNIQUE NOT NULL"
            ")"
        )
        connection.commit()

        cursor.close()


        cursor = connection.cursor()

        cursor.execute(
            "DROP TABLE PerfTest"
        )
        connection.commit()

        cursor.close()

        cursor = connection.cursor()

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS PerfTest ("
                "id SERIAL PRIMARY KEY,"
                "name TEXT,"
                "email TEXT"
            ")"
        )
        connection.commit()

        cursor.close()


        



        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO PerfTest "
                "(name, email)"
                " VALUES ("
                    "'host',"
                    "'hostinger'"
                ")"
        )

        connection.commit()
        cursor.close()
    
    with mongo.create_connection() as connection:
        docs = connection["RAG"]
        coll = docs["perftest"]


        coll.insert_one({"name": "host", "email": "hostinger"})

    with redis.open_session() as session:
        session.hset("user:1", mapping={"name": "host", "email": "hostinger"})


def test_read(number_of_operations: int = 100) -> tuple[float, float, float]:


    # 1. PostgresSQL
    print("Measure Postgres")
    postgres_timer: Timer = Timer()
    postgres_timer.start()

    for i in range(number_of_operations):
        with postgres.create_connection("rag") as connection:
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM PerfTest WHERE name = 'host'")

    postgres_timer.stop()
    print("")


    # 2. MongoDB
    print("Measure Mongo")
    mongo_timer: Timer = Timer()
    mongo_timer.start()

    for i in range(number_of_operations):
        print(f"{i+1:>6}/{number_of_operations}", end="\r")
        with mongo.create_connection() as connection:
            db = connection["RAG"]
            coll = db["perftest"]


            coll.find_one({"name": "host"})

    mongo_timer.stop()
    print("")

    # 3. Redis
    print("Measure Redis")
    redis_timer: Timer = Timer()
    redis_timer.start()
    for i in range(number_of_operations):
        print(f"{i+1:>6}/{number_of_operations}", end="\r")
        with redis.open_session() as session:
            session.hgetall("user:1")

    redis_timer.stop()
    print("")

    return postgres_timer.duration, mongo_timer.duration, redis_timer.duration



def test_update(number_of_operations: int = 100) -> tuple[float, float, float]:


    # 1. PostgresSQL
    print("Measure Postgres")
    postgres_timer: Timer = Timer()
    postgres_timer.start()

    for i in range(number_of_operations):
        with postgres.create_connection("rag") as connection:
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            cursor = connection.cursor()

            cursor.execute(
                "UPDATE PerfTest "
                    f"SET name = 'hosthaha{i}'"
                    "WHERE id = 1"
            )

            connection.commit()
            cursor.close()

    postgres_timer.stop()
    print("")


    # 2. MongoDB
    print("Measure Mongo")
    mongo_timer: Timer = Timer()
    mongo_timer.start()

    for i in range(number_of_operations):
        print(f"{i+1:>6}/{number_of_operations}", end="\r")
        with mongo.create_connection() as connection:
            db = connection["RAG"]
            coll = db["perftest"]


            coll.update_one({"name": "host"}, {"$set": {"name": f"hosthahahah{i}"}})

    mongo_timer.stop()
    print("")

    # 3. Redis
    print("Measure Redis")
    redis_timer: Timer = Timer()
    redis_timer.start()
    for i in range(number_of_operations):
        print(f"{i+1:>6}/{number_of_operations}", end="\r")
        with redis.open_session() as session:
            session.hset(f"user:1", mapping={"name": f"host{i}", "email": "hostinger"})

    redis_timer.stop()
    print("")

    return postgres_timer.duration, mongo_timer.duration, redis_timer.duration

def test_write(number_of_operations: int = 100) -> tuple[float, float, float]:


    # 1. PostgresSQL
    print("Measure Postgres")
    postgres_timer: Timer = Timer()
    postgres_timer.start()

    for i in range(number_of_operations):
        with postgres.create_connection("rag") as connection:
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO PerfTest "
                    "(name, email)"
                    " VALUES ("
                        f"'host{i}',"
                        f"'hostinger{i}'"
                    ")"
            )

            connection.commit()
            cursor.close()

    postgres_timer.stop()
    print("")


    # 2. MongoDB
    print("Measure Mongo")
    mongo_timer: Timer = Timer()
    mongo_timer.start()

    for i in range(number_of_operations):
        print(f"{i+1:>6}/{number_of_operations}", end="\r")
        with mongo.create_connection() as connection:
            db = connection["RAG"]
            coll = db["perftest"]


            coll.insert_one({"name": f"host{i}", "email": f"hostinger{i}"})

    mongo_timer.stop()
    print("")

    # 3. Redis
    print("Measure Redis")
    redis_timer: Timer = Timer()
    redis_timer.start()
    for i in range(number_of_operations):
        print(f"{i+1:>6}/{number_of_operations}", end="\r")
        with redis.open_session() as session:
            session.hset(f"user:{i+2}", mapping={"name": f"host{i}", "email": f"hostinger{i}"})

    redis_timer.stop()
    print("")

    return postgres_timer.duration, mongo_timer.duration, redis_timer.duration


def base_operation(number_of_operations: int = 100) -> tuple[float, float, float]:

    # 1. PostgresSQL
    postgres_timer: Timer = Timer()
    postgres_timer.start()

    for _ in range(number_of_operations):
        with postgres.create_connection("RAG") as connection:
            cursor = connection.cursor()
            pass

    postgres_timer.stop()


    # 2. MongoDB
    mongo_timer: Timer = Timer()
    mongo_timer.start()

    for _ in range(number_of_operations):
        with mongo.create_connection() as connection:
            pass

    mongo_timer.stop()

    # 3. Redis
    redis_timer: Timer = Timer()
    redis_timer.start()
    for _ in range(number_of_operations):
        with redis.open_session() as session:
            pass

    redis_timer.stop()

    return postgres_timer.duration, mongo_timer.duration, redis_timer.duration


def base_operation2(number_of_operations: int = 100) -> tuple[float, float, float]:

    # 1. PostgresSQL
    postgres_timer: Timer = Timer()
    postgres_timer.start()

    for _ in range(number_of_operations):
        pass

    postgres_timer.stop()


    # 2. MongoDB
    mongo_timer: Timer = Timer()
    mongo_timer.start()

    for _ in range(number_of_operations):
        pass

    mongo_timer.stop()

    # 3. Redis
    redis_timer: Timer = Timer()
    redis_timer.start()
    for _ in range(number_of_operations):
        pass

    redis_timer.stop()

    return postgres_timer.duration, mongo_timer.duration, redis_timer.duration