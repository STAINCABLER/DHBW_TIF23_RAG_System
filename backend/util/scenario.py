import dataclasses

@dataclasses.dataclass
class ScenarioQuestion(object):
    id: int
    scenario_id: int
    question: str
    response: str
    embedding: list[float]

    @classmethod
    def from_dict(cls, data) -> "ScenarioQuestion":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in dataclasses.fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        return cls(**filtered_data)

    def to_dict(self) -> dict[str, any]:
        return dataclasses.asdict(self)

@dataclasses.dataclass
class Scenario(object):
    id: int
    name: str
    description: str

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
