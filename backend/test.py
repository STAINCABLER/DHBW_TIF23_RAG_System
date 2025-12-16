import sys
sys.dont_write_bytecode = True
# import util.database_setup
# import database.redis

# util.database_setup.setup()


# import ragutil.scenario_search





# r = ragutil.scenario_search.match_keywords([
#     "Finanzmanagement",
#     "Kundenverwaltung",
#     "Gesundheitswesen"
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

    #coll.drop()

    r = coll.find({}, {"embedding": 0})
    
    for i in r:
        print(i)
        print("\n\n")


# import ragutil.perplexity
# import dotenv

# dotenv.load_dotenv()



# r = ragutil.perplexity.PerplexityQuerier()


# s = r.prompt("Was ist eine Datenbank")
# print(s)

# import setup.database_setup
# import setup.scenario_setup


# setup.database_setup.setup_tables()
# setup.scenario_setup.setup_scenarios()


# import setup.chunker
# setup.chunker.import_all()


# import logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)s | %(message)s",
#     handlers=[
#         logging.StreamHandler(sys.stdout),
#     ],
# )
# import rag
# prompt: str = "Ich möchte eine Datenbank haben. Hierfür habe ich im Wald über 100 Temperaturmessgeräte, welche in einem refgelmäßifen Interval Daten zukommen lassen. Welche Datenbankarchitektur ist dafür geeingnet?"

# prompt = "Ich verwalte viele Server als DDos Schutz. Alle meine Kunden benötigen sehr schnell eine Überprüfung, ob ein Client eine Verbindung aufbauen darf. Des Weiteren benötige ich eine Datenbank über meine Kunden."
# prompt = "Wir möchten als Projekt ein Datenbank RAG bauen, welches Informationen über Datenbanken ausgeben kann. Die Nutzereingabe wird hierbei so verarbeitet, dass aus dem RAG passende Daten gefunden werden. Diese sollen zusammen mit der Nutzereingabe an ein LLm geschickt werden zur Textverarbeitung."

# prompt = "Wie würdest du ein RAG Datenbanksystem machen?"
# szf = rag.rag_process(prompt)


# print(szf)