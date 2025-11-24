import pymongo
import contextlib
import collections.abc

@contextlib.contextmanager
def create_connection() -> collections.abc.Generator[pymongo.MongoClient, any, any]:
    cli = pymongo.MongoClient("mongodb://db-mongo:27017/")
    yield cli
    cli.close()
