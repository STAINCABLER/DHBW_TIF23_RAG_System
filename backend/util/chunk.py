import dataclasses

@dataclasses.dataclass
class ChunkFragment(object):
    chunk_id: int
    document_id: int
    section_title: str
    text: str
    position: int
    keywords: str
    version: str
    embedding: str
