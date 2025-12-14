import bson.objectid
import pgvector.psycopg2.vector
import torch

import database.mongo
import util.chunk
import util.embedding
import util.scenario

def build_pipeline_from_vector_list(vector_list: list[float], number_of_chunks: int = 5) -> list:

    pipeline = [
        {
            "$addFields": {
                "similarity": {
                    "$reduce": {
                        "input": {"$range": [0, 384]},
                        "initialValue": 0,
                        "in": {
                            "$add": [
                                "$$value",
                                {
                                    "$multiply": [
                                        {"$arrayElemAt": ["$embedding", "$$this"]},
                                        {"$arrayElemAt": [vector_list, "$$this"]}
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        },
        {"$sort": {"similarity": -1}},

        # Hier Anzahl eingeben
        {"$limit": number_of_chunks},
        
        {"$project": {"embedding_id": 1, "similarity": 1}}
    ]

    return pipeline

def build_pipeline_from_embedding(tensor: torch.Tensor) -> list:
    vector: pgvector.psycopg2.vector.Vector = pgvector.psycopg2.vector.Vector(tensor)
    return build_pipeline_from_vector_list(vector.to_list())




RAW_DATA: list[dict[str, any]] = [
    {
        "chunk_id": 100,
        "content": "Das ist mein Brot",
        "keywords": "Kundendaten, Hamster"
    },
    {
        "chunk_id": 101,
        "content": "Mein Auto ist schön",
        "keywords": "Katze, Himmel"
    }
]

def setup() -> None:
    for i in RAW_DATA:
        print("Docker 1")
        tensor: torch.Tensor = util.embedding.build_embedding(i["keywords"])
        vector: pgvector.psycopg2.vector.Vector = pgvector.psycopg2.vector.Vector(tensor)
        i["embedding"] = vector.to_list()
    

        with database.mongo.create_connection() as conn:
            db = conn["rag"]
            coll = db["chunks"]

            coll.insert_one(i)


def retrieve_raw_chunks_for_scenario_question(scenario_question: util.scenario.ScenarioQuestion, number_of_chunks: int = 5) -> list[dict[str, any]]:
    vector_list: list[float] = scenario_question.embedding

    pipeline: list = build_pipeline_from_vector_list(vector_list, number_of_chunks)

    with database.mongo.create_connection() as conn:
        db = conn["rag"]
        coll = db["chunks"]

        return list(coll.aggregate(pipeline))

def retrieve_chunks_for_scenario_question(scenario_question: util.scenario.ScenarioQuestion, number_of_chunks: int = 5) -> list[util.chunk.DocumentChunk]:
    vector_list: list[float] = scenario_question.embedding

    pipeline: list = build_pipeline_from_vector_list(vector_list, number_of_chunks)

    with database.mongo.create_connection() as conn:
        db = conn["rag"]
        coll = db["chunks"]

        raw_chunks: list[dict[str, any]] = list(coll.aggregate(pipeline))

    chunks: list[util.chunk.DocumentChunk] = []

    for raw_chunk in raw_chunks:
        chunk: util.chunk.DocumentChunk = util.chunk.DocumentChunk.load_from_id(raw_chunk["_id"])
        chunks.append(chunk)
    
    return chunks


def convert_raw_chunks(raw_chunks: list[dict[str, any]]) -> list[util.chunk.DocumentChunk]:
    chunks: list[util.chunk.DocumentChunk] = []

    for raw_chunk in raw_chunks:
        with database.mongo.create_connection() as conn:
            db = conn["rag"]
            coll = db["chunks"]

            chunk_data: dict[str, any] = coll.find_one({"_id": raw_chunk["_id"]})

        chunk: util.chunk.DocumentChunk = util.chunk.DocumentChunk.from_dict(chunk_data)
        chunks.append(chunk)
    
    return chunks

def search_chunks_for_scenario_with_reduction(scenario: util.scenario.Scenario) -> list[util.chunk.DocumentChunk]:
    similarity_map: dict[bson.objectid.ObjectId, float] = {}

    questions: list[util.scenario.ScenarioQuestion] = scenario.get_scenario_questions()

    for question in questions:
        raw_result = retrieve_raw_chunks_for_scenario_question(question)
        for i in raw_result:
            id: bson.objectid.ObjectId = i["_id"]
            similarity: float = i["similarity"]

            if not id in similarity_map:
                similarity_map[id] = 0.0
            similarity_map[id] += similarity
    
    sorted_chunks: dict[bson.objectid.ObjectId, int] = dict(sorted(similarity_map.items(), key=lambda item: item[1], reverse=True))

    reduced_chunks: list = []

    if len(sorted_chunks) <= 10:
        reduced_chunks = sorted_chunks.keys()
    else:
        reduced_chunks = sorted_chunks.keys()[0:10]
    
    chunks: list[util.chunk.DocumentChunk] = [
        util.chunk.DocumentChunk.load_from_id(key)
        for key in reduced_chunks
    ]

    return chunks


def search_chunks_for_scenario(scenario: util.scenario.Scenario) -> list:
    questions: list[util.scenario.ScenarioQuestion] = scenario.get_scenario_questions()

    for question in questions:
        raw_result = retrieve_raw_chunks_for_scenario_question(question)
        for i in raw_result:
            id: bson.objectid.ObjectId = i["_id"]
            similarity: float = i["similarity"]
    
    sorted_chunks: dict[bson.objectid.ObjectId, int] = dict(sorted(similarity_map.items(), key=lambda item: item[1], reverse=True))

    if len(sorted_chunks) <= 10:
        return sorted_chunks
    return sorted_chunks[0:10]

def test() -> None:

    input: str = "Miezekatze"
    tensor: torch.Tensor = util.embedding.build_embedding(input)

    pipeline: list = build_pipeline_from_embedding(tensor)
    with database.mongo.create_connection() as conn:
        db = conn["rag"]
        coll = db["chunks"]

        result = list(coll.aggregate(pipeline))

        s = str(result[0]["_id"])
        print(result[0])
        d = {}

        d[bson.objectid.ObjectId(s)] = 0.897
        d[bson.objectid.ObjectId(s)] += 0.988
        print(d)
        #print(coll.find_one({"_id": bson.objectid.ObjectId(s)}))
                
                # list(collection.aggregate(pipeline))