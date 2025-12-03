import util
from access import mongo
import time

def next_element(amount: int):
    inner_amount: int = 100
    for i in range(amount):
        data: list[dict[str, any]] = [
            {"name": f"host{j+i*inner_amount+200}", "email": f"hostinger{j+i*inner_amount+200}"}
            for j in range(inner_amount)
        ]
        yield i, data

class MongoTester(util.BaseTester):
    def __init__(self) -> None:
        super().__init__()
        self.db_name: str = "MongoDB"

    def setup(self) -> None:
        with mongo.create_connection() as connection:
            docs = connection["RAG"]
            coll = docs["perftest"]


            coll.insert_one({"name": "host", "email": "hostinger"})

    def test_read(self, number_of_operations: int = 100) -> float:
        print("Read Test")
        mongo_timer: util.Timer = util.Timer()
        mongo_timer.start()

        for i in range(number_of_operations):
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            with mongo.create_connection() as connection:
                db = connection["RAG"]
                coll = db["perftest"]


                coll.find_one({"name": "host"})

        mongo_timer.stop()
        print("")

        return mongo_timer.duration

    def test_write(self, number_of_operations: int = 100) -> float:
        print("Write Test")
        mongo_timer: util.Timer = util.Timer()
        mongo_timer.start()

        for i in range(number_of_operations):
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            with mongo.create_connection() as connection:
                db = connection["RAG"]
                coll = db["perftest"]


                coll.insert_one({"name": f"host{i}", "email": f"hostinger{i}"})

        mongo_timer.stop()
        print("")

        return mongo_timer.duration

    def test_update(self, number_of_operations: int = 100) -> float:
        print("Update Test")
        mongo_timer: util.Timer = util.Timer()
        mongo_timer.start()

        for i in range(number_of_operations):
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            with mongo.create_connection() as connection:
                db = connection["RAG"]
                coll = db["perftest"]


                coll.update_one({"name": "host"}, {"$set": {"name": f"hosthahahah{i}"}})

        mongo_timer.stop()
        print("")

        return mongo_timer.duration

    def test_bulk_read(self, number_of_operations: int = 100) -> float:
        print("Bulk Read Test")
        mongo_timer: util.Timer = util.Timer()
        mongo_timer.start()

        for i in range(number_of_operations):
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            with mongo.create_connection() as connection:
                db = connection["RAG"]
                coll = db["perftest"]


                r = coll.find({ "name": { "$regex": "host[0-9]+" } })
                for i in r:
                    pass

        mongo_timer.stop()
        print("")

        return mongo_timer.duration

    def test_bulk_write(self, number_of_operations: int = 100) -> float:
        number_of_operations = int(number_of_operations / 10)
        print("Bulk Write Test")

        data: list[list[dict[str, any]]] = [
            [{"name": f"host{i+j*number_of_operations+200}", "email": f"hostinger{i+j*number_of_operations+200}"}
            for i in range(100)
            ]
            for j in range(number_of_operations)
        ]

        mongo_timer: util.Timer = util.Timer()
        mongo_timer.start()

        for i in range(number_of_operations):
            print(f"{i+1:>6}/{number_of_operations}", end="\r")
            with mongo.create_connection() as connection:
                db = connection["RAG"]
                coll = db["perftest"]

                coll.insert_many(data[i])
                time.sleep(1)

        mongo_timer.stop()
        print("")

        return mongo_timer.duration * 10
