import csv
import json
import logging
import pgvector.psycopg2.vector
import torch
import uuid

import database.mongo
import util.embedding
import util.file_manager


def process_file(file_path: str) -> None:
    logging.info(file_path)  
    content: list | dict = read_file_content_csv(file_path)

    chunk_csv(content, file_path.split("/")[-1])

def read_file_content_csv(file_path: str) -> list[dict[str, any]]:
    with open(util.file_manager.get_relative_file_path(file_path), "r", encoding="utf-8") as file:
        dict_reader = csv.DictReader(file)
        
        list_of_dict = list(dict_reader)

        return list_of_dict

def batching(data, batch_size):
    current_datas: list = []
    current_size: int = 0
    for i in data:
        current_datas.append(i)
        current_size += 1
        if current_size >= batch_size:
            yield current_datas
            current_datas = []
            current_size = 0
    
    if current_size > 0:
        yield current_datas
        



def chunk_csv(content: list[dict[str, any]], file_name: str) -> None:

    doc_id: str = str(uuid.uuid4())

    chunks: list[dict[str, any]] = []

    for i, batch in enumerate(batching(content, 5)):
        chunk_id: str = str(uuid.uuid4())

        content: str = json.dumps(batch)
        character_count: int = len(content)

        tensor: torch.Tensor = util.embedding.build_embedding(content)
        vector: pgvector.psycopg2.vector.Vector = pgvector.psycopg2.vector.Vector(tensor)

        chunk: dict[str, any] = {
            "chunk_id": chunk_id,
            "document_id": doc_id,
            "chunk_index": i,
            "chunk_text": content,
            "token_count": character_count,
            "character_count": character_count,
            "embedding": vector.to_list(),
            "metadata": {
                "heading": f"{file_name}",
                "section": f"{i}",
                "page_number": 1,
                "source_file": file_name,
                "language": "DE"
            }
        }

        chunks.append(chunk)
    print(f"Identified {len(chunks)} elements in {file_name}")

    with database.mongo.create_connection() as conn:
        db = conn["rag"]
        coll = db["chunks"]

        coll.insert_many(chunks)
