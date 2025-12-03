import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, List

import psycopg2
from psycopg2.extensions import connection as PsycopgConnection
from sentence_transformers import SentenceTransformer

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


if __name__ == "__main__":
    sys.exit(main())