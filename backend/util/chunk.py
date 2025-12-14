import bson.objectid
import dataclasses

import database.mongo

@dataclasses.dataclass
class DocumentChunkMetadata(object):
    heading: str
    section: str
    page_number: int
    source_file: str
    language: str

    @classmethod
    def from_dict(cls, data) -> "DocumentChunkMetadata":
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
class DocumentChunk(object):
    """
    Chunks are stored in a MongoDB
    rag::chunks
    """
    chunk_id: str
    document_id: str
    chunk_index: 0
    chunk_text: str
    token_count: int
    character_count: int
    metadata: DocumentChunkMetadata

    @staticmethod
    def load_from_id(_id: bson.objectid.ObjectId) -> "DocumentChunk":
        with database.mongo.create_connection() as conn:
            db = conn["rag"]
            coll = db["chunks"]

            chunk_data: dict[str, any] = coll.find_one({"_id": _id}, projection={"embedding": False})

            if not chunk_data:
                return None
            return DocumentChunk.from_dict(chunk_data)

    @classmethod
    def from_dict(cls, data) -> "DocumentChunk":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in dataclasses.fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        filtered_data["metadata"] = DocumentChunkMetadata.from_dict(filtered_data["metadata"])
        return cls(**filtered_data)

    def to_dict(self) -> dict[str, any]:
        return dataclasses.asdict(self)
