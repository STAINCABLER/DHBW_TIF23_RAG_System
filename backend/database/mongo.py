import contextlib
import os
import pymongo


MONGO_HOST: str = os.getenv("MONGO_HOST", "127.0.0.1")

@contextlib.contextmanager
def create_connection():
    mongo_client: pymongo.MongoClient = pymongo.MongoClient(f"mongodb://127.0.0.1:27017/?directConnection=true&appName=mongosh")
    yield mongo_client
    mongo_client.close()
