"""
Docstring for backend.rag.scenario_search

Input: Keywords from se LLM
Output: 3 Szenarios
"""
import pgvector.psycopg2
import pgvector.psycopg2.vector
import torch

import database.postgres
import util.embedding
import util.scenario


def match_keywords(keywords: list[str]) -> list[util.scenario.Scenario]:
    keyword_vectors: list[pgvector.psycopg2.vector.Vector] = []

    query_parts: list[str] = []
    single_query_part: str = "1 - (embedding <-> %s)"

    for keyword in keywords:

        embedding: torch.Tensor = util.embedding.build_embedding(keyword)
        vector: pgvector.psycopg2.vector.Vector = pgvector.psycopg2.vector.Vector(embedding.tolist())

        keyword_vectors.append(vector)

        query_parts.append(single_query_part)
    
    
    similarity_filter: str = " + ".join(query_parts)

    with database.postgres.create_connection("rag") as conn:
        cursor = conn.cursor()
        pgvector.psycopg2.register_vector(conn)

        cursor.execute(
            "SELECT "
                "id, "
                "name, "
                "description, "
                f"({similarity_filter}) AS similarity "
            "FROM scenarios "
            "ORDER BY similarity DESC LIMIT 3;",
            tuple(keyword_vectors)
        )

        results = cursor.fetchall()
        column_names = [col[0] for col in cursor.description]

        scenarios: list[util.scenario.Scenario] = []

        if results:
            print("\nNew results")
            for row in results:
                raw_result: dict[str, any] = dict(zip(column_names, row))

                scenario_name: str = raw_result["name"]
                similarity: float = raw_result["similarity"]

                print(f"{similarity:.5f}: {scenario_name}")

                scenario: util.scenario.Scenario = util.scenario.Scenario.from_dict(raw_result)
                scenarios.append(scenario)

        return scenarios
