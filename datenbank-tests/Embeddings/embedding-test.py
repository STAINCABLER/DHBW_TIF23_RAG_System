import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, List

import psycopg2
from psycopg2.extensions import connection as PsycopgConnection
from sentence_transformers import SentenceTransformer

from pgvector.psycopg2 import register_vector
from pgvector.psycopg2.vector import Vector


vvvvvvvvraw: dict[str, str] = {
        "scenario_name": "Kundendaten",
        "scenario_description": "",
        "data_type": "structured",
        "access_method": "read/write heavy",
        "tags": [
            "CONSISTENCY",
            "CRITICAL"
        ]
    }


def load_data() -> list[dict[str, any]]:
    with open(Path(__file__).with_name("raw_data.json"), "rb") as file:
        return json.load(file)

def build_embed_vector_phrase(data: dict[str, any]) -> str:
    scenario_name: str = data["scenario_name"]
    scenario_description: str = data["scenario_description"]
    data_type: str = data["data_type"]
    access_method: str = data["access_method"]
    tags: list[str] = data["tags"]
    
    joined_tags: str = ",".join(tags)

    #query: str = f"scenario_name:'{scenario_name}';scenario_description:'{scenario_description}';data_type:'{data_type}';access_method:'{access_method}';tags:'{joined_tags}';"
    #query: str = f"scenario_name:'{scenario_name}';scenario_description:'{scenario_description}';tags:'{joined_tags}';"
    query: str = f"{scenario_name};{scenario_description}"
    return query

def insert_embedddddddd(
        conn: PsycopgConnection,
        model: SentenceTransformer,
        data: dict[str, any]
    ) -> None:
    register_vector(conn)
    query_string: str = build_embed_vector_phrase(data)
    with conn.cursor() as cursor:
        ensure_faq_table(cursor)
        cursor.execute("SELECT 1 FROM scenarios WHERE name = %s", (data["scenario_name"],))
        if cursor.fetchone():
            logger.info("Skipping existing question: %s", data["scenario_name"])
            return

        vector = model.encode(query_string)
        embedding = [float(value) for value in vector]

        cursor.execute(
            "INSERT INTO scenarios (name, description, data_type, access_method, tags, embedding) VALUES (%s, %s, %s, %s, %s, %s)",
            (data["scenario_name"], data["scenario_description"], data["data_type"], data["access_method"], data["tags"], embedding),
        )

        logger.info("Inserted question '%s' (embedding length %d)", data["scenario_name"], len(embedding))

    conn.commit()

DEFAULT_QUESTIONS = (
    "How do I reset my password?",
    "How to change my billing plan?",
)

DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_DSN = "dbname=test user=postgres password=postgres"

LOG_FILE = Path(__file__).with_name("embedding-test.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Mirror log output to both the console and the log file for easy debugging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("embedding_test")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for database and model configuration."""

    parser = argparse.ArgumentParser(
        description="Generate sentence-transformer embeddings and store them in PostgreSQL.",
    )
    parser.add_argument(
        "--dsn",
        default=os.getenv("EMBEDDING_DB_DSN", DEFAULT_DSN),
        help=(
            "PostgreSQL DSN, e.g. 'postgresql://user:pass@host:5432/db'. "
            "Defaults to the EMBEDDING_DB_DSN environment variable or '%(default)s'."
        ),
    )
    parser.add_argument(
        "--model-name",
        default=os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL),
        help="SentenceTransformer model name to load.",
    )
    parser.add_argument(
        "--questions-file",
        type=Path,
        help="Path to a text file containing one question per line (leading '#' comments are ignored).",
    )
    return parser.parse_args()


def load_questions(path: Path) -> List[str]:
    """Load question prompts from a text file."""

    questions: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                questions.append(stripped)

    if not questions:
        raise ValueError(f"No questions found in {path}")

    return questions


def ensure_faq_table(cursor: psycopg2.extensions.cursor) -> None:
    """Create the target table if it does not already exist."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scenarios (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            embedding vector(384) NOT NULL,
            data_type TEXT,
            access_method TEXT,
            tags TEXT[]
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS faq (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            embedding DOUBLE PRECISION[] NOT NULL
        )
        """
    )


def insert_embeddings(
    conn: PsycopgConnection,
    questions: Iterable[str],
    model: SentenceTransformer,
) -> int:
    """Insert embeddings for the provided questions, returning the number of new rows."""

    inserted = 0
    with conn.cursor() as cursor:
        ensure_faq_table(cursor)

        for question in questions:
            cursor.execute("SELECT 1 FROM faq WHERE question = %s", (question,))
            if cursor.fetchone():
                logger.info("Skipping existing question: %s", question)
                continue

            vector = model.encode(question)
            embedding = [float(value) for value in vector]

            cursor.execute(
                "INSERT INTO faq (question, embedding) VALUES (%s, %s)",
                (question, embedding),
            )

            inserted += 1
            logger.info("Inserted question '%s' (embedding length %d)", question, len(embedding))

    conn.commit()
    return inserted


def get_embed(
    conn: PsycopgConnection,
    question: str,
    model: SentenceTransformer,
) -> any:
    """Insert embeddings for the provided questions, returning the number of new rows."""
    register_vector(conn)
    with conn.cursor() as cursor:
        ensure_faq_table(cursor)
        # cursor.execute("SELECT 1 FROM faq WHERE question = %s", (question,))
        # i = cursor.fetchone()
        # if i:
        #     logger.info("Found existing question: %s", question)
        #     return i

        #vector = model.encode(question)
        #embedding = [float(value) for value in vector]

        vector = model.encode(question).tolist()
        embedding = Vector(vector)

        cursor.execute(
            "SELECT id, name, (1 - (embedding <-> %s) + 1 - (embedding <-> %s)) AS similarity FROM scenarios ORDER BY similarity DESC LIMIT 3;", (embedding,embedding,)
        )

        i = cursor.fetchall()
        return i

        inserted += 1
        logger.info("Inserted question '%s' (embedding length %d)", question, len(embedding))

    return None

def search() -> int:
    args = parse_args()

    try:
        model = SentenceTransformer(args.model_name)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to load model '%s'", args.model_name)
        return 1

    #question: str = "Wie kann ich ein System zum Austauschen von Texten nutzen, damit alle Mitarbeiter diese bekommen"
    #question: str = "Ich möchte ein System, welches die Sitzungen meines Webservers managed"
    try:
        with psycopg2.connect(args.dsn) as conn:
            inserted = get_embed(conn, question, model)
            logger.info(str(inserted))
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Database operation failed: %s", exc)
        return 1

    #logger.info("Embedding test completed. Inserted %d new rows.", inserted)
    return 0

def scenarios_insert_test() -> int:
    args = parse_args()

    try:
        model = SentenceTransformer(args.model_name)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to load model '%s'", args.model_name)
        return 1

    question: str = "What is my password?"
    data = load_data()
    try:
        with psycopg2.connect(args.dsn) as conn:
            for dt in data:
                insert_embedddddddd(conn, model, dt)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Database operation failed: %s", exc)
        return 1

    #logger.info("Embedding test completed. Inserted %d new rows.", inserted)
    return 0

def main() -> int:
    args = parse_args()

    try:
        questions = (
            load_questions(args.questions_file)
            if args.questions_file
            else list(DEFAULT_QUESTIONS)
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to load questions: %s", exc)
        return 1

    logger.info("Loaded %d questions", len(questions))

    try:
        model = SentenceTransformer(args.model_name)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to load model '%s'", args.model_name)
        return 1

    try:
        with psycopg2.connect(args.dsn) as conn:
            inserted = insert_embeddings(conn, questions, model)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Database operation failed: %s", exc)
        return 1

    logger.info("Embedding test completed. Inserted %d new rows.", inserted)
    return 0



question: str = "Vertraulich"

if __name__ == "__main__":
    print("HIER GANZ UNTEN NUR DAS AUSSUCHEN; WAS UAUCH GENUTZT WERDEN SOLL!! (embedding-test.py ganz unten)")
    print("Das hierige Docker compose sollte laufen (user -> postgres, password -> password)")
    # main() -> fügt die testfargen ein
    # search() -> Sucht nach der Frage, welche in der Methode angegeben ist (aber in scenarios-tabelle)
    # scenarios_insert_test() -> Fügt die in raw_data.json angegebenen Scenarien in die DB ein

    
    #sys.exit(main())
    #sys.exit(search())
    sys.exit(scenarios_insert_test())