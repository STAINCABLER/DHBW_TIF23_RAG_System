import json
import pgvector.psycopg2.vector
import torch
import uuid
import logging

import database.mongo
import util.embedding
import util.file_manager



def process_file(file_path: str) -> None:
    logging.info(file_path)
    content: list | dict = read_file_content_json(file_path)

    chunk_json(content, file_path.split("/")[-1])

def read_file_content_json(file_path: str) -> list | dict:
    with open(util.file_manager.get_relative_file_path(file_path), "rb") as file:
       return json.load(file)

def chunk_json(data: dict[str, any] | list[any], file_name: str) -> None:

    doc_id: str = str(uuid.uuid4())

    chunks: list[dict[str, any]] = []
    print(f"Identified {len(data)} elements in {file_name}")

    for i, key in enumerate(data):
        if isinstance(data, dict):
            value = data[key]
        else:
            value = key
            key = ""

        chunk_id: str = str(uuid.uuid4())

        content: str = json.dumps(value)
        character_count: int = len(content)

        tensor: torch.Tensor = util.embedding.build_embedding(f"{key}: {content}")
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
                "heading": key,
                "section": f"key:{i}",
                "page_number": 1,
                "source_file": file_name,
                "language": "DE"
            }
        }

        chunks.append(chunk)

    with database.mongo.create_connection() as conn:
        db = conn["rag"]
        coll = db["chunks"]

        coll.insert_many(chunks)
