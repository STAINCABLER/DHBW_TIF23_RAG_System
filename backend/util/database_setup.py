import hashlib
import database.postgres



def setup() -> None:
    setup_tables()
    setup_values()

def setup_tables() -> None:
    does_type_exist = database.postgres.fetch_one(
        "SELECT EXISTS (SELECT 1 from pg_type where typname = 'profile_type');"
    )
    if not does_type_exist["exists"]:
        database.postgres.execute(
            "CREATE TYPE profile_type AS ENUM ("
                "'student',"
                "'professional',"
                "'researcher'"
            ");"
        )

    database.postgres.execute(
        "CREATE TABLE IF NOT EXISTS users ("
            "id SERIAL PRIMARY KEY,"
            "username VARCHAR(255) UNIQUE NOT NULL,"
            "email VARCHAR(255) UNIQUE NOT NULL,"
            "password_hash VARCHAR(255) NOT NULL,"
            "profile_type profile_type NOT NULL,"
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
            "last_login TIMESTAMP,"
            "is_active BOOLEAN DEFAULT TRUE,"
            "preferences JSONB"
        ");"
    )

def setup_values() -> None:

    does_user_exist = database.postgres.fetch_one(
        "SELECT EXISTS (SELECT 1 from users where username = 'user');"
    )

    if not does_user_exist["exists"]:
        username: str = "user"
        email: str = "user@dhbw.de"
        password: str = "user"
        profile_type: str = "student"
        password_hash: str = hashlib.sha256(password.encode()).hexdigest()

        database.postgres.execute(
            "INSERT INTO users ("
                "username,"
                "email,"
                "password_hash,"
                "profile_type"
            ") "
            "VALUES ( "
                f"'{username}', "
                f"'{email}', "
                f"'{password_hash}', "
                f"'{profile_type}'"
            ")"
        )
