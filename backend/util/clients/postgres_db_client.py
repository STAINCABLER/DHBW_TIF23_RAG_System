import psycopg2
import contextlib


@contextlib.contextmanager
def create_connection(database_name: str):
    connection = psycopg2.connect(
        database=database_name,
        host="db-postgres",
        user="postgres",
        password="password",
        port="5432"
    )
    yield connection
    connection.close()


def execute(query: str, database_name: str = "rag") -> None:

    with create_connection(database_name=database_name) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()


def fetch_one(query: str, database_name: str = "rag") -> list[dict[str, any]]:
    result = []

    with create_connection(database_name=database_name) as connection:
        cursor = connection.cursor()
        cursor.execute(query)

        results = cursor.fetchone()
        column_names = [col[0] for col in cursor.description]

        if results:
            result = dict(zip(column_names, results))
    
    return result

def fetch_all(query: str, database_name: str = "rag") -> list[dict[str, any]]:
    result = []

    with create_connection(database_name=database_name) as connection:
        cursor = connection.cursor()
        cursor.execute(query)

        results = cursor.fetchall()
        column_names = [col[0] for col in cursor.description]

        if results:

            for row in results:
                result.append(dict(zip(column_names, row)))

        
    
    return result
        