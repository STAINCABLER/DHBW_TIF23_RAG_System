import contextlib
import os
import psycopg2

POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")

@contextlib.contextmanager
def create_connection(database_name: str):
    connection = psycopg2.connect(
        database=database_name,
        host=POSTGRES_HOST,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port="5432"
    )
    yield connection
    connection.close()
