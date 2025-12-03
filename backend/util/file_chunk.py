import dataclasses
import uuid

@dataclasses.dataclass
class FileChunkMetadata(object):
    doc_id: uuid.UUID
    chunk_id: uuid.UUID
    position: int
    section_title: str
    keywords: list[str]

@dataclasses.dataclass
class FileChunk(object):
    chunk_metadata: FileChunkMetadata
    content: str

    @classmethod
    def from_dict(cls, data) -> "UploadedFile":
        filtered_data = {
            f.name: data[f.name.lower()] if f.name.lower() in data else data[f.name]
            for f in dataclasses.fields(cls)
            if f.name.lower() in data
            or f.name in data
        }
        for field in dataclasses.fields(cls):
            if field.name.lower() not in filtered_data:
                filtered_data[field.name.lower()] = None
        return cls(**filtered_data)

    def to_dict(self) -> dict[str, any]:
        raw_dict: dict[str, any] = dataclasses.asdict(self)

        raw_dict["file_uuid"] = str(self.file_uuid)
        raw_dict["uploaded_at"] = self.uploaded_at.isoformat()

        return raw_dict
