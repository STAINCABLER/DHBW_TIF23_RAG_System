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
            """
            CREATE TYPE profile_type AS ENUM (
                'student',
                'professional',
                'researcher'
            )
            """
        )

    # Users-Tabelle
    database.postgres.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            profile_type profile_type NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            preferences JSONB
        )
        """
    )

    # Conversations-Tabelle
    database.postgres.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        """
    )

    # Messages-Tabelle
    database.postgres.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            message_id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
            role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        )
        """
    )

    # Uploaded-Files-Tabelle
    database.postgres.execute(
        """
        CREATE TABLE IF NOT EXISTS uploaded_files (
            file_id SERIAL PRIMARY KEY,
            conversation_id INTEGER REFERENCES conversations(conversation_id) ON DELETE SET NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_uuid UUID NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            is_processed BOOLEAN DEFAULT FALSE,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Scenarios-Tabelle
    database.postgres.execute(
        """
        CREATE TABLE IF NOT EXISTS scenarios (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            embedding vector(384) NOT NULL,
        )
        """
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
            f"""
            INSERT INTO users (
                username,
                email,
                password_hash,
                profile_type
            )
            VALUES (
                '{username}',
                '{email}',
                '{password_hash}',
                '{profile_type}'
            )
            """
        )
