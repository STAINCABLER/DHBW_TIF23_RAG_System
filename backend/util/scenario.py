import dataclasses
import json

import database.postgres

@dataclasses.dataclass
class ScenarioQuestion(object):
    """
    ScenarioQuestions are stored in a PGVectorDB
    rag::scenario_questions
    """
    id: int
    scenario_id: int
    question: str
    answer: str
    embedding: list[float]

    @classmethod
    def from_dict(cls, data) -> "ScenarioQuestion":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in dataclasses.fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        # Conversion to list[float]
        if "embedding" in filtered_data:
            filtered_data["embedding"] = json.loads(filtered_data["embedding"])

        return cls(**filtered_data)

    def to_dict(self) -> dict[str, any]:
        return dataclasses.asdict(self)

@dataclasses.dataclass
class Scenario(object):
    """
    Scenarios are stored in a PGVectorDB
    rag::scenarios
    """
    id: int
    name: str
    description: str

    def get_scenario_questions(self) -> list[ScenarioQuestion]:
        raw_questions: list[dict[str, any]] = database.postgres.fetch_all(
            """
            SELECT * FROM scenario_questions
            WHERE scenario_id = %s
            """,
            "rag",
            (self.id,)
        )
        return [
            ScenarioQuestion.from_dict(i)
            for i in raw_questions
        ]

    @classmethod
    def from_dict(cls, data) -> "Scenario":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in dataclasses.fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        return cls(**filtered_data)

    def to_dict(self) -> dict[str, any]:
        return dataclasses.asdict(self)
