import pgvector.psycopg2.vector
import torch
import uuid
import logging

import database.mongo
import util.embedding
import util.file_manager



def process_file(file_path: str) -> None:
    logging.info(file_path)
    content: str = read_file_content_txt(file_path)

    chunk_txt(content, file_path.split("/")[-1])

def read_file_content_txt(file_path: str) -> list | dict:
    with open(util.file_manager.get_relative_file_path(file_path), "r", encoding="utf-8") as file:
       return file.read()
def chunk_txt(data: str, file_name: str) -> None:

    doc_id: str = str(uuid.uuid4())

    if "\r\n" in data:
        raw_data: list[str] = data.split("\r\n\r\n")
    else:
        raw_data: list[str] = data.split("\n\n")
    

    main_title: str = raw_data[0]

    del raw_data[0]

    chunks: list[dict[str, any]] = []
    print(f"Identified {len(raw_data)} elements in {file_name}")

    for i, raw_text in enumerate(raw_data):

        previous_text: str = ""
        next_text: str = ""

        if i > 0:
            previous_raw_text: str = raw_data[i - 1]
            first_char_index: int = int(len(previous_raw_text) * 0.9)

            first_char_index: int = previous_raw_text.find(" ", first_char_index)
            if first_char_index > 0:
                previous_text = previous_raw_text[first_char_index:]
        
        if i < len(raw_data) - 1:
            next_raw_text: str = raw_data[i + 1]
            first_char_index: int = int(len(next_raw_text) * 0.1)

            first_char_index: int = next_raw_text.find(" ", first_char_index)
            if first_char_index > 0:
                next_text = next_raw_text[:first_char_index]
        

        full_text: str = f"{previous_text}\n{raw_text}\n{next_text}"



        chunk_id: str = str(uuid.uuid4())

        if "\r\n" in raw_text:
            section_name: str = raw_text.split("\r\n")[0]
        else:
             section_name: str = raw_text.split("\n")[0]

        character_count: int = len(full_text)

        tensor: torch.Tensor = util.embedding.build_embedding(f"{main_title}-{section_name}: {full_text}")
        vector: pgvector.psycopg2.vector.Vector = pgvector.psycopg2.vector.Vector(tensor)

        chunk: dict[str, any] = {
            "chunk_id": chunk_id,
            "document_id": doc_id,
            "chunk_index": i,
            "chunk_text": full_text,
            "token_count": character_count,
            "character_count": character_count,
            "embedding": vector.to_list(),
            "metadata": {
                "heading": f"{main_title}-{section_name}",
                "section": f"{main_title}-{section_name}-{i}",
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
