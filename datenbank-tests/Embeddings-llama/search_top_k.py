"""
search_top_k.py
Sucht die K ähnlichsten Chunks zu einer Query using pgvector Cosine Distance.

Siehe: /documentation/datenbanken/06_PostgreSQL_Vektorembeddings.md
SQL: ORDER BY embedding <=> query_embedding LIMIT K
"""

import os
import logging
from typing import List, Dict, Any

import psycopg2
from pgvector.psycopg2 import register_vector
from dotenv import load_dotenv

from query_embedding import QueryEmbedder

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "rag_db")
DB_USER = os.getenv("DB_USER", "rag_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rag_pass")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VectorSearch:
    """Performs similarity search against rag.chunk using pgvector."""

    def __init__(self):
        self.query_embedder = QueryEmbedder()

    def get_db_connection(self):
        """Establish connection with pgvector support."""
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        register_vector(conn)
        return conn

    def search_top_k(
        self,
        query: str,
        k: int = 3,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for the top-k most similar chunks.

        Args:
            query: The search query string
            k: Number of results to return (default: 3 for top-3)
            threshold: Minimum cosine similarity threshold (0.0 = no threshold)

        Returns:
            List of dicts with: document_id, chunk_index, content, similarity_score
        """
        logger.info(f"Searching for top-{k} similar chunks: '{query}'")

        # Step 1: Embed the query
        q_embedding = self.query_embedder.embed_query(query)

        # Step 2: Query pgvector
        conn = self.get_db_connection()
        cur = conn.cursor()

        try:
            # Cosine distance in pgvector: <=>
            # Similarity = 1 - distance (for normalized embeddings)
            sql = """
                SELECT
                    document_id,
                    chunk_index,
                    content,
                    1 - (embedding <=> %s) AS cosine_similarity
                FROM rag.chunk
                WHERE 1 - (embedding <=> %s) >= %s
                ORDER BY embedding <=> %s
                LIMIT %s;
            """

            cur.execute(sql, (q_embedding, q_embedding, threshold, q_embedding, k))
            rows = cur.fetchall()

            results = []
            for doc_id, chunk_idx, content, similarity in rows:
                results.append({
                    "document_id": doc_id,
                    "chunk_index": chunk_idx,
                    "content": content,
                    "similarity_score": float(similarity)
                })

            logger.info(f"Found {len(results)} chunks above threshold {threshold}")
            return results

        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise
        finally:
            cur.close()
            conn.close()

    def search_top_k_with_filter(
        self,
        query: str,
        k: int = 3,
        document_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search top-k but optionally filter by document_id.
        Useful if you want results only from specific documents.
        """
        logger.info(f"Searching for top-{k} chunks with filters: '{query}'")

        q_embedding = self.query_embedder.embed_query(query)
        conn = self.get_db_connection()
        cur = conn.cursor()

        try:
            if document_ids:
                placeholders = ",".join(["%s"] * len(document_ids))
                sql = f"""
                    SELECT
                        document_id,
                        chunk_index,
                        content,
                        1 - (embedding <=> %s) AS cosine_similarity
                    FROM rag.chunk
                    WHERE document_id IN ({placeholders})
                    ORDER BY embedding <=> %s
                    LIMIT %s;
                """
                params = [q_embedding] + document_ids + [q_embedding, k]
            else:
                sql = """
                    SELECT
                        document_id,
                        chunk_index,
                        content,
                        1 - (embedding <=> %s) AS cosine_similarity
                    FROM rag.chunk
                    ORDER BY embedding <=> %s
                    LIMIT %s;
                """
                params = [q_embedding, q_embedding, k]

            cur.execute(sql, params)
            rows = cur.fetchall()

            results = []
            for doc_id, chunk_idx, content, similarity in rows:
                results.append({
                    "document_id": doc_id,
                    "chunk_index": chunk_idx,
                    "content": content,
                    "similarity_score": float(similarity)
                })

            return results

        except Exception as e:
            logger.error(f"Error during filtered search: {e}")
            raise
        finally:
            cur.close()
            conn.close()


# ============ Main ============

if __name__ == "__main__":
    searcher = VectorSearch()

    # Example queries
    test_queries = [
        "Wie funktioniert das RAG-System?",
        "Was ist pgvector?",
        "Embeddings und Vektoren"
    ]

    print("\n=== Top-3 Similarity Search Results ===\n")

    for test_query in test_queries:
        results = searcher.search_top_k(test_query, k=3)

        print(f"Query: '{test_query}'")
        print("-" * 80)

        if results:
            for i, result in enumerate(results, 1):
                print(f"\n  [{i}] Similarity: {result['similarity_score']:.4f}")
                print(f"      Document: {result['document_id']}")
                print(f"      Chunk #{result['chunk_index']}")
                print(f"      Content: {result['content'][:150]}...")
        else:
            print("  No results found")

        print("\n" + "=" * 80 + "\n")
