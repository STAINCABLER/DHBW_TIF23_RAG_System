import pgvector.psycopg2.vector
import torch

import database.mongo
import util.chunk
import util.scenario

def build_pipeline_from_vector_list(vector_list: list[float], number_of_chunks: int = 5) -> list:
    pipeline = [
        {
            "$vectorSearch": {
            "index": "vec_idx",
            "path": "embedding",
            "queryVector": vector_list,
            "numCandidates": 100,
            "limit": number_of_chunks
            }
        }
    ]

    return pipeline

def build_pipeline_from_embedding(tensor: torch.Tensor) -> list:
    vector: pgvector.psycopg2.vector.Vector = pgvector.psycopg2.vector.Vector(tensor)
    return build_pipeline_from_vector_list(vector.to_list())


def retrieve_chunks_for_scenario_question(scenario_question: util.scenario.ScenarioQuestion, number_of_chunks: int = 5) -> list[util.chunk.DocumentChunk]:
    vector_list: list[float] = scenario_question.embedding

    pipeline: list = build_pipeline_from_vector_list(vector_list, number_of_chunks)

    with database.mongo.create_connection() as conn:
        db = conn["rag"]
        coll = db["chunks"]

        raw_chunks: list[dict[str, any]] = list(coll.aggregate(pipeline))

    chunks: list[util.chunk.DocumentChunk] = []

    for raw_chunk in raw_chunks:
        chunk: util.chunk.DocumentChunk = util.chunk.DocumentChunk.from_dict(raw_chunk)
        chunks.append(chunk)
    
    return chunks
