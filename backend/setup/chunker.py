import os

import database.mongo
import time
import setup.chunks.csv_chunker
import setup.chunks.json_chunker
import setup.chunks.md_chunker
import setup.chunks.txt_chunker

import util.file_manager




def import_all() -> None:
    start_time: float = time.perf_counter()
    do_csv()
    do_json()
    do_md()
    do_txt()



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
    
    delta = time.perf_counter() - start_time
    print(f"Chunking all took {delta:.3f} Seconds")
    


def do_csv() -> None:
    base_path: str = util.file_manager.get_relative_file_path("ingest/csv")

    files_csv: list[str] = os.listdir(base_path)

    print(files_csv)

    for file_name in files_csv:
        setup.chunks.csv_chunker.process_file(base_path + "/" + file_name)

def do_json() -> None:
    base_path: str = util.file_manager.get_relative_file_path("ingest/json")

    files_json: list[str] = os.listdir(base_path)

    print(files_json)

    for file_name in files_json:
        setup.chunks.json_chunker.process_file(base_path + "/" + file_name)


def do_md() -> None:
    base_path: str = util.file_manager.get_relative_file_path("ingest/md")

    files_md: list[str] = os.listdir(base_path)

    print(files_md)

    for file_name in files_md:
        setup.chunks.md_chunker.process_file(base_path + "/" + file_name)

def do_txt() -> None:
    base_path: str = util.file_manager.get_relative_file_path("ingest/txt")

    files_txt: list[str] = os.listdir(base_path)

    print(files_txt)

    for file_name in files_txt:
        setup.chunks.txt_chunker.process_file(base_path + "/" + file_name)




