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


def execute(query: str, database_name: str = "rag") -> None:

    with create_connection(database_name=database_name) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()


def fetch_one(query: str, database_name: str = "rag", args: tuple[any] = None) -> dict[str, any]:
    result = []

    with create_connection(database_name=database_name) as connection:
        cursor = connection.cursor()
        cursor.execute(query, args)

        results = cursor.fetchone()
        column_names = [col[0] for col in cursor.description]

        if results:
            result = dict(zip(column_names, results))
    
    return result

def fetch_all(query: str, database_name: str = "rag", args: tuple[any] = None) -> list[dict[str, any]]:
    result = []

    with create_connection(database_name=database_name) as connection:
        cursor = connection.cursor()
        cursor.execute(query, args)

        results = cursor.fetchall()
        column_names = [col[0] for col in cursor.description]

        if results:

            for row in results:
                result.append(dict(zip(column_names, row)))

        
    
    return result
        