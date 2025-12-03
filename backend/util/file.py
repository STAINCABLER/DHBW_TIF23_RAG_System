import dataclasses
import datetime
import os
import uuid

import database.postgres

UPLOAD_FOLDER: str = os.getenv("UPLOAD_PATH", "./backend/upload")

@dataclasses.dataclass
class UploadedFile(object):
    file_id: int
    conversation_id: int
    original_filename: str
    file_uuid: uuid.UUID
    file_type: str
    is_processed: bool
    uploaded_at: datetime.datetime

    def delete_file(self) -> None:
        database.postgres.execute(
            "DELETE FROM uploaded_files "
            f"WHERE file_id = {self.file_id}"
        )

        file_path: str = os.path.join(UPLOAD_FOLDER, str(self.file_uuid))
        os.remove(file_path)

    def get_file_path(self) -> str:
        return os.path.join(UPLOAD_FOLDER, str(self.file_uuid))

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
    @staticmethod
    def find_by_file_id(file_id: int) -> "UploadedFile":
        result: dict[str, any] = database.postgres.fetch_one(
            "SELECT * "
            "FROM uploaded_files "
            f"WHERE file_id = {file_id}"
        )

        if not result:
            return None

        return UploadedFile.from_dict(result)

    def to_dict(self) -> dict[str, any]:
        raw_dict: dict[str, any] = dataclasses.asdict(self)

        raw_dict["file_uuid"] = str(self.file_uuid)
        raw_dict["uploaded_at"] = self.uploaded_at.isoformat()

        return raw_dict
