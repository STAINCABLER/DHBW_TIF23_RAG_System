"""
embeddings_ingest.py
Konvertiert Dokument‑Chunks in Embeddings und speichert sie in PostgreSQL mit pgvector.

Siehe Dokumentation: /documentation/datenbanken/06_PostgreSQL_Vektorembeddings.md
Schema: rag.chunk (id, document_id, chunk_index, content, embedding)
"""

import os
import logging
from typing import List, Tuple
from dataclasses import dataclass

import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# ============ Configuration ============

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "rag_db")
DB_USER = os.getenv("DB_USER", "rag_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rag_pass")

# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dimensional
EMBEDDING_DIMENSION = 384

# Chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============ Models ============

@dataclass
class ChunkRecord:
    """Represents a single chunk with metadata."""
    document_id: str
    chunk_index: int
    content: str
    embedding: List[float]


# ============ Database ============

def get_db_connection():
    """Establish connection to PostgreSQL with pgvector support."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    register_vector(conn)
    return conn


def init_schema():
    """Create rag schema and chunk table if they don't exist."""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Create extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create schema
        cur.execute("CREATE SCHEMA IF NOT EXISTS rag;")

        # Create chunk table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rag.chunk (
                id SERIAL PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INT NOT NULL,
                content TEXT NOT NULL,
                embedding vector(%d) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """ % EMBEDDING_DIMENSION)

        # Create index for efficient similarity search (HNSW)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunk_embedding 
            ON rag.chunk USING hnsw (embedding vector_cosine_ops)
            WITH (m=4, ef_construction=20);
        """)

        conn.commit()
        logger.info("Schema initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing schema: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# ============ Embedding ============

def load_embedding_model():
    """Load the sentence transformer model."""
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"Model loaded. Dimension: {model.get_sentence_embedding_dimension()}")
    return model


def embed_texts(texts: List[str], model: SentenceTransformer) -> List[List[float]]:
    """
    Generate normalized embeddings for multiple texts.
    Normalized embeddings are optimal for cosine similarity in pgvector.
    """
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [emb.tolist() for emb in embeddings]


# ============ Chunking ============

def chunk_text(text: str, max_chars: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks.
    Implements the chunking strategy from: /documentation/datenbanken/03_PostgreSQL_Dokumentation.md
    """
    text = text.strip()

    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


# ============ Ingest ============

def ingest_document(
    document_id: str,
    full_text: str,
    model: SentenceTransformer,
    batch_size: int = 32
) -> int:
    """
    Ingest a document:
    1. Split into chunks
    2. Generate embeddings
    3. Store in rag.chunk table
    
    Returns: Number of chunks inserted
    """
    logger.info(f"Ingesting document: {document_id}")

    # Step 1: Chunk
    chunks = chunk_text(full_text, max_chars=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    logger.info(f"Created {len(chunks)} chunks from document")

    # Step 2: Embed
    logger.info("Generating embeddings...")
    embeddings = embed_texts(chunks, model)

    # Step 3: Insert into DB
    conn = get_db_connection()
    cur = conn.cursor()
    inserted = 0

    try:
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            cur.execute(
                """
                INSERT INTO rag.chunk (document_id, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (document_id, i, chunk, emb)
            )
            inserted += 1

            if (i + 1) % batch_size == 0:
                conn.commit()
                logger.info(f"Inserted {inserted} chunks...")

        conn.commit()
        logger.info(f"Successfully inserted {inserted} chunks for document '{document_id}'")

    except Exception as e:
        logger.error(f"Error inserting chunks: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    return inserted


# ============ Main ============

if __name__ == "__main__":
    # Initialize schema
    init_schema()

    # Load model
    model = load_embedding_model()

    # Example: Ingest a sample document
    sample_doc_id = "doc_001_rag_architecture"
    sample_text = """
    Retrieval-Augmented Generation (RAG) ist ein System, das Dokumentensuche mit 
    Sprachmodellerstellung kombiniert. Das DHBW RAG System nutzt PostgreSQL mit pgvector 
    für effiziente Vektorsuche. Dokumente werden in Chunks aufgeteilt, in Embeddings 
    konvertiert und mit Cosine Similarity verglichen, um relevante Treffer zu finden.
    
    Die Architektur besteht aus mehreren Komponenten:
    1. Chunk‑Generierung: Dokumente werden in semantisch sinnvolle Teile zerlegt
    2. Embedding‑Generierung: Jeder Chunk wird in einen Vektor umgewandelt
    3. Speicherung: Embeddings werden in pgvector gespeichert
    4. Retrieval: Anfragen werden nach ähnlichen Chunks durchsucht
    5. LLM‑Kontextualisierung: Die gefundenen Chunks werden dem LLM als Kontext gegeben
    """

    ingest_document(sample_doc_id, sample_text, model)
