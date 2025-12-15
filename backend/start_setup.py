print("Inprting LIBs")
import setup.database_setup
import setup.scenario_setup

import setup.chunker




print("Setup DBS")
setup.database_setup.setup_tables()

print("Import Scenarios")
setup.scenario_setup.setup_scenarios()

print("Import Chunks")
setup.chunker.import_all()