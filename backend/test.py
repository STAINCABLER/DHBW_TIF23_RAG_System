import sys
sys.dont_write_bytecode = True
# import util.database_setup
# import database.redis

# util.database_setup.setup()


# import ragutil.scenario_search





# r = ragutil.scenario_search.match_keywords([
#     "Emails",
#     "Überwachung",
#     "Vertraulich",
#     "Datenbank"
# ])

# for i in r:
#     print(i)

#import ragutil.chunks_search


#ragutil.chunks_search.setup()
#ragutil.chunks_search.test()

# r = ragutil.scenario_search.match_keywords([
#     "Emails",
#     "Überwachung",
#     "Vertraulich",
#     "Datenbank"
# ])

# for i in r:
#     print(i)


# import database.postgres

# r = database.postgres.fetch_one("SELECT embedding FROM scenarios LIMIT 1")
# import json

# print(json.loads(r["embedding"]))

# import ragutil.chunks_search

# ragutil.chunks_search.test()

# i = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

# print(i[0:10])


import database.mongo


with database.mongo.create_connection() as conn:
    db = conn["rag"]
    coll = db["chunks"]

    r = coll.find(projection={"_id": 1})
    print(list(r))
