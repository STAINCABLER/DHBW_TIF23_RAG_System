import util
from access import postgres

class PostgresTester(util.BaseTester):
    def __init__(self) -> None:
        super().__init__()
        self.db_name: str = "Postgres"

    def setup(self) -> None:
        with postgres.create_connection("rag") as connection:
            cursor = connection.cursor()

            cursor.execute(
                "CREATE TABLE IF NOT EXISTS PerfTest ("
                    "id SERIAL PRIMARY KEY,"
                    "name TEXT,"
                    "email TEXT"
                ")"
            )
            connection.commit()

            cursor.close()


            cursor = connection.cursor()

            cursor.execute(
                "DROP TABLE PerfTest"
            )
            connection.commit()

            cursor.close()

            cursor = connection.cursor()

            cursor.execute(
                "CREATE TABLE IF NOT EXISTS PerfTest ("
                    "id SERIAL PRIMARY KEY,"
                    "name TEXT,"
                    "email TEXT"
                ")"
            )
            connection.commit()

            cursor.close()

            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO PerfTest "
                    "(name, email)"
                    " VALUES ("
                        "'host',"
                        "'hostinger'"
                    ")"
            )

            connection.commit()
            cursor.close()

    def test_read(self, number_of_operations: int = 100) -> float:
        print("Read Test")
        postgres_timer: util.Timer = util.Timer()
        postgres_timer.start()

        for i in range(number_of_operations):
            with postgres.create_connection("rag") as connection:
                print(f"{i+1:>6}/{number_of_operations}", end="\r")
                cursor = connection.cursor()

                cursor.execute("SELECT * FROM PerfTest WHERE name = 'host'")

        postgres_timer.stop()
        print("")

        return postgres_timer.duration

    def test_write(self, number_of_operations: int = 100) -> float:
        print("Write Test")
        postgres_timer: util.Timer = util.Timer()
        postgres_timer.start()

        for i in range(number_of_operations):
            with postgres.create_connection("rag") as connection:
                print(f"{i+1:>6}/{number_of_operations}", end="\r")
                cursor = connection.cursor()

                cursor.execute(
                    "INSERT INTO PerfTest "
                        "(name, email)"
                        " VALUES ("
                            f"'host{i}',"
                            f"'hostinger{i}'"
                        ")"
                )

                connection.commit()
                cursor.close()

        postgres_timer.stop()
        print("")

        return postgres_timer.duration

    def test_update(self, number_of_operations: int = 100) -> float:
        print("Update Test")
        postgres_timer: util.Timer = util.Timer()
        postgres_timer.start()

        for i in range(number_of_operations):
            with postgres.create_connection("rag") as connection:
                print(f"{i+1:>6}/{number_of_operations}", end="\r")
                cursor = connection.cursor()

                cursor.execute(
                    "UPDATE PerfTest "
                        f"SET name = 'hosthaha{i}'"
                        "WHERE id = 1"
                )

                connection.commit()
                cursor.close()

        postgres_timer.stop()
        print("")

        return postgres_timer.duration

    def test_bulk_read(self, number_of_operations: int = 100) -> float:
        print("Bulk Read Test")
        postgres_timer: util.Timer = util.Timer()
        postgres_timer.start()

        for i in range(number_of_operations):
            with postgres.create_connection("rag") as connection:
                print(f"{i+1:>6}/{number_of_operations}", end="\r")
                cursor = connection.cursor()

                cursor.execute(
                    "SELECT * FROM PerfTest "
                    "WHERE id < 100"
                )

                cursor.close()

        postgres_timer.stop()
        print("")

        return postgres_timer.duration

    def test_bulk_write(self, number_of_operations: int = 100) -> float:
        print("Bulk Write Test")

        data_list: list[str] = [
            f"('host{i}', 'hostinger{i}')"
            for i in range(100)
        ]
        query_body: str = ",".join(data_list)
        postgres_timer: util.Timer = util.Timer()
        postgres_timer.start()

        for i in range(number_of_operations):
            with postgres.create_connection("rag") as connection:
                print(f"{i+1:>6}/{number_of_operations}", end="\r")
                cursor = connection.cursor()

                cursor.execute(
                    "INSERT INTO PerfTest "
                        "(name, email)"
                        " VALUES "
                        + query_body
                )

                connection.commit()
                cursor.close()

        postgres_timer.stop()
        print("")

        return postgres_timer.duration