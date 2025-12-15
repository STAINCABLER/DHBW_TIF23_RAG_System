import json
import langchain_text_splitters
import langchain_core.documents
import pgvector.psycopg2.vector
import torch
import uuid

import database.mongo
import util.embedding
import util.file_manager

def process_file(file_path: str) -> None:
    content: str = read_file_content_json(file_path)

    chunk_md(content, file_path.split("/")[-1])

def read_file_content_json(file_path: str) -> list | dict:
    with open(util.file_manager.get_relative_file_path(file_path), "r", encoding="utf-8") as file:
       return file.read()

def strategy_heading_aware(text: str, chunk_size: int = 0, overlap: int = 0) -> list[langchain_core.documents.Document]:
    headers_to_split_on = [
        ("##", "Header 2"),
    ]
    markdown_splitter = langchain_text_splitters.MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    return markdown_splitter.split_text(text)


def chunk_md(data: str, file_name: str) -> None:    
    doc_id: str = str(uuid.uuid4())

    chunks: list[langchain_core.documents.Document] = strategy_heading_aware(data)

    for i, raw_chunk in enumerate(chunks):
        chunk_id: str = str(uuid.uuid4())
        
        header_info = raw_chunk.metadata.get('Header 2', 'N/A')

        content: str = json.dumps(raw_chunk.page_content)
        character_count: int = len(content)

        tensor: torch.Tensor = util.embedding.build_embedding(f"{header_info}: {content}")
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
                "heading": header_info,
                "section": f"key:{i}",
                "page_number": 1,
                "source_file": file_name,
                "language": "DE"
            }
        }

        with database.mongo.create_connection() as conn:
            db = conn["rag"]
            coll = db["chunks"]

            coll.insert_one(chunk)
