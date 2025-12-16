import os

import database.mongo
import setup.chunks.csv_chunker
import setup.chunks.json_chunker
import setup.chunks.md_chunker

import util.file_manager




def import_all() -> None:
    do_csv()
    do_json()
    do_md()



    # Create Index
    with database.mongo.create_connection() as conn:
        db = conn["rag"]

        db.command(
            {
                "createSearchIndexes": "chunks",
                "indexes": [
                    {
                        "name": "vec_idx",
                        "definition": {
                            "mappings": {
                                "dynamic": False,
                                "fields": {
                                    "embedding": {
                                        "type": "vector",
                                        "similarity": "cosine",
                                        "numDimensions": 384
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        )
    


def do_csv() -> None:
    base_path: str = util.file_manager.get_relative_file_path("ingest/csv")

    files_json: list[str] = os.listdir(base_path)

    print(files_json)
    print(base_path)

    for file_name in files_json:
        setup.chunks.csv_chunker.process_file(base_path + "/" + file_name)

def do_json() -> None:
    base_path: str = util.file_manager.get_relative_file_path("ingest/json")

    files_json: list[str] = os.listdir(base_path)

    print(files_json)
    print(base_path)

    for file_name in files_json:
        setup.chunks.json_chunker.process_file(base_path + "/" + file_name)


def do_md() -> None:
    base_path: str = util.file_manager.get_relative_file_path("ingest/md")

    files_json: list[str] = os.listdir(base_path)

    print(files_json)
    print(base_path)

    for file_name in files_json:
        setup.chunks.md_chunker.process_file(base_path + "/" + file_name)





