import database.postgres


def setup_tables() -> None:
    # Scenarios-Tabelle
    database.postgres.execute(
        """
        CREATE TABLE IF NOT EXISTS scenarios (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            embedding VECTOR(384)
        )
        """
    )

    # ScenarioQuestions-Tabelle
    database.postgres.execute(
        """
        CREATE TABLE IF NOT EXISTS scenario_questions (
            id BIGSERIAL PRIMARY KEY,
            scenario_id BIGINT NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            answer TEXT,
            embedding VECTOR(384)
        )
        """
    )


