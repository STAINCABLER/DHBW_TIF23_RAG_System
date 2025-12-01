import time
from access import mongo, postgres, redis





with mongo.create_connection() as conn:
    db = conn["RAG"]
    coll = db["perftest"]


    for i in coll.find():
        print(i)

