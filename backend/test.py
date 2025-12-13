import sys
sys.dont_write_bytecode = True
# import util.database_setup
# import database.redis

# util.database_setup.setup()


import ragutil.scenario_search





r = ragutil.scenario_search.match_keywords([
    "Emails",
    "Überwachung",
    "Vertraulich",
    "Datenbank"
])

for i in r:
    print(i)


