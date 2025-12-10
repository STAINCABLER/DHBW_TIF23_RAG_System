"""
query_embedding.py
Erzeugt ein Embedding für eine Nutzeranfrage, using the same model and normalization
as the document ingestion.

Siehe: /documentation/datenbanken/06_PostgreSQL_Vektorembeddings.md (Retrieval-Phase)
"""

import os
import logging
from typing import List

from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryEmbedder:
    """Handles query embedding using the same model as document ingestion."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        logger.info(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.dimension}")

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query string.
        Uses normalize_embeddings=True to match document embedding generation.
        """
        embedding = self.model.encode([query], normalize_embeddings=True)[0]
        return embedding.tolist()

    def embed_queries(self, queries: List[str]) -> List[List[float]]:
        """Embed multiple queries."""
        embeddings = self.model.encode(queries, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]


# ============ Main ============

if __name__ == "__main__":
    embedder = QueryEmbedder()

    # Example queries
    test_queries = [
        "Wie funktioniert das RAG-System?",
        "Was ist pgvector?",
        "Wie werden Embeddings generiert?"
    ]

    print("\n=== Query Embeddings ===\n")
    for query in test_queries:
        emb = embedder.embed_query(query)
        print(f"Query: {query}")
        print(f"Embedding Dimension: {len(emb)}")
        print(f"First 5 values: {emb[:5]}")
        print()
