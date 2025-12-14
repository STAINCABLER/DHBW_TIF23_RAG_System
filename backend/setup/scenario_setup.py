import json
import os.path
import pathlib
import pgvector.psycopg2
import pgvector.psycopg2.vector
import time
import torch


import database.postgres
import util.embedding

FILE_LOCATION: str = "data/scenarios.json"


def setup_scenarios() -> None:

    scenarios: list[dict[str, any]] = load_scenarios_from_file()
    print("Starting Inserting Scenarios")
    start_time: float = time.perf_counter()
    for scenario in scenarios["scenarios"]:
        scenario_id: int = insert_scenario(scenario)

        questions: list[dict[str, any]] = scenario["questions"]

        insert_scenario_questions(scenario_id, questions)
    
    end_time: float = time.perf_counter()

    diff_time: float = end_time - start_time

    print(f"Loading Scenarios took {diff_time:.3f} Seconds")




def load_scenarios_from_file() -> list[dict[str, any]]:

    with open(os.path.join(pathlib.Path(__file__).parent, FILE_LOCATION), "rb") as file:
       return json.load(file)


def insert_scenario(data: dict[str, any]) -> int:
    scenario_name: str = data["name"]
    scenario_description: str = data["description"]
    scenario_embedding_string: str = f"{scenario_name};{scenario_description}"

    tensor: torch.Tensor = util.embedding.build_embedding(scenario_embedding_string)
    vector: pgvector.psycopg2.vector.Vector = pgvector.psycopg2.vector.Vector(tensor)
    embedding = vector.to_list()

    with database.postgres.create_connection("rag") as conn:
        pgvector.psycopg2.register_vector(conn)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO scenarios
                (name, description, embedding)
            VALUES (%s, %s, %s)
            """,
            (data["name"], data["description"], embedding),
        )

        conn.commit()
    
    scenario_id: int = database.postgres.fetch_one(
        """
        SELECT id FROM scenarios
        WHERE name = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        "rag",
        (scenario_name,)
    )["id"]

    return scenario_id


def insert_scenario_questions(scenario_id: int, questions: list[dict[str, any]]) -> None:
    for question in questions:

        tensor: torch.Tensor = util.embedding.build_embedding(question["response"])
        vector: pgvector.psycopg2.vector.Vector = pgvector.psycopg2.vector.Vector(tensor)
        embedding = vector.to_list()

        with database.postgres.create_connection("rag") as conn:
            pgvector.psycopg2.register_vector(conn)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO scenario_questions
                    (scenario_id, question, answer, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (scenario_id, question["question"], question["response"], embedding),
            )

            conn.commit()

