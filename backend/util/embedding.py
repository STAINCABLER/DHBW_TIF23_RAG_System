import sentence_transformers
import torch


DEFAULT_MODEL = "all-MiniLM-L6-v2"

model: sentence_transformers.SentenceTransformer = sentence_transformers.SentenceTransformer(DEFAULT_MODEL)


def build_embedding(content: str) -> torch.Tensor:
    return model.encode(content)
    