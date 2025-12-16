print("Inprting LIBs")
import database.mongo
import database.postgres
import setup.database_setup
import setup.scenario_setup

import setup.chunker
import sys
import logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(message)s",
#     handlers=[
#         logging.StreamHandler(sys.stdout),
#     ],
# )

def reset_dbs() -> None:
    try:
        database.postgres.execute(
            "DROP TABLE scenarios CASCADE"
        )
    except:
        pass

    try:
        database.postgres.execute(
            "DROP TABLE scenario_questions"
        )
    except:
        pass

    with database.mongo.create_connection() as conn:
        db = conn["rag"]
        db.drop_collection("chunks")

reset_dbs()

print("Setup DBS")
setup.database_setup.setup_tables()

print("Import Scenarios")
setup.scenario_setup.setup_scenarios()

print("Import Chunks")
setup.chunker.import_all()