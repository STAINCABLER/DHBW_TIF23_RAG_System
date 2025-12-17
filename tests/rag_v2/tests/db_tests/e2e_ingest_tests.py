"""
End-to-End Ingest Performance Tests
====================================

Diese Tests führen den KOMPLETTEN RAG-Ingest-Prozess durch:
1. Datei-Parsing (MD, TXT, JSON, CSV, PDF)
2. Chunking (Fixed-Size und Semantic)
3. ECHTE Embedding-Generierung (sentence-transformers)
4. Speicherung in Datenbanken (Redis, MongoDB, PostgreSQL/pgvector)
5. Vektor-Suche (Similarity Search)

WARUM: Nur End-to-End-Tests zeigen das reale Systemverhalten.
       Isolierte Unit-Tests können Integrationsprobleme übersehen.

HYPOTHESE:
    - MongoDB ist schneller beim Speichern vieler kleiner Dokumente
    - PostgreSQL/pgvector bietet präzisere Vektor-Suche
    - Redis ist am schnellsten für Cache-ähnliche Zugriffe

REFERENZ: Modul 6 (Chunking), Modul 7 (Embeddings), Modul 8 (Polyglot)

Autor: RAG Performance Test Suite
"""

import time
import json
import csv
import logging
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any
from abc import ABC, abstractmethod

# Datenbank-Clients
import redis
import pymongo
import psycopg2
import numpy as np

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import TestResult, ns_to_ms

logger = logging.getLogger(__name__)


# =============================================================================
# Embedding Generator (Echt mit sentence-transformers)
# =============================================================================

class EmbeddingGenerator:
    """
    Echte Embedding-Generierung mit sentence-transformers.
    
    Verwendet all-MiniLM-L6-v2 (384 Dimensionen) - schnell und effektiv.
    Fallback auf Mock-Embeddings wenn Modell nicht verfügbar.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.dimensions = 384  # MiniLM-L6-v2 default
        self._load_model()
    
    def _load_model(self) -> None:
        """Lädt das Embedding-Modell."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Lade Embedding-Modell: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            self.dimensions = self.model.get_sentence_embedding_dimension()
            logger.info(f"✓ Modell geladen: {self.dimensions} Dimensionen")
        except ImportError:
            logger.warning("sentence-transformers nicht installiert - verwende Mock-Embeddings")
            self.model = None
        except Exception as e:
            logger.warning(f"Modell konnte nicht geladen werden: {e} - verwende Mock-Embeddings")
            self.model = None
    
    def generate(self, text: str) -> list[float]:
        """Generiert Embedding für einen Text."""
        if self.model is not None:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        else:
            # Fallback: deterministisches Mock-Embedding
            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            vec = rng.randn(self.dimensions).astype('float32')
            vec = vec / np.linalg.norm(vec)
            return vec.tolist()
    
    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generiert Embeddings für mehrere Texte."""
        if self.model is not None:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings.tolist()
        else:
            return [self.generate(text) for text in texts]


# =============================================================================
# Datei-Parser (inklusive PDF)
# =============================================================================

class FileParser:
    """Parser für alle unterstützten Dateiformate inkl. PDF."""
    
    @staticmethod
    def parse_markdown(file_path: Path) -> str:
        """Liest Markdown-Datei."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def parse_txt(file_path: Path) -> str:
        """Liest Text-Datei."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def parse_json(file_path: Path) -> str:
        """Liest JSON und konvertiert zu Text."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return FileParser._json_to_text(data)
    
    @staticmethod
    def _json_to_text(data: Any, depth: int = 0) -> str:
        """Rekursive JSON zu Text Konvertierung."""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{key}:")
                    lines.append(FileParser._json_to_text(value, depth + 1))
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            return "\n".join(FileParser._json_to_text(item, depth) for item in data)
        else:
            return str(data)
    
    @staticmethod
    def parse_csv(file_path: Path) -> str:
        """Liest CSV und konvertiert zu Text."""
        texts = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_text = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
                texts.append(row_text)
        return "\n\n".join(texts)
    
    @staticmethod
    def parse_pdf(file_path: Path) -> str:
        """
        Liest PDF mit PyMuPDF.
        
        Extrahiert Text aus allen Seiten.
        """
        try:
            import pymupdf
        except ImportError:
            try:
                import fitz as pymupdf  # Alternativer Import-Name
            except ImportError:
                logger.warning(f"PyMuPDF nicht installiert - überspringe PDF: {file_path}")
                return ""
        
        try:
            doc = pymupdf.open(str(file_path))
            text = ""
            for page in doc:
                text += page.get_text("text")
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Fehler beim PDF-Parsing {file_path}: {e}")
            return ""
    
    @staticmethod
    def parse(file_path: Path) -> str:
        """Parst Datei basierend auf Endung."""
        suffix = file_path.suffix.lower()
        
        parsers = {
            '.md': FileParser.parse_markdown,
            '.txt': FileParser.parse_txt,
            '.json': FileParser.parse_json,
            '.csv': FileParser.parse_csv,
            '.pdf': FileParser.parse_pdf,
        }
        
        parser = parsers.get(suffix)
        if parser:
            return parser(file_path)
        else:
            logger.warning(f"Nicht unterstütztes Format: {suffix}")
            return ""


# =============================================================================
# Chunking
# =============================================================================

@dataclass
class Chunk:
    """Ein Text-Chunk mit Metadaten."""
    id: str
    content: str
    source_file: str
    chunk_index: int
    embedding: Optional[list] = None
    metadata: dict = field(default_factory=dict)


class Chunker:
    """Teilt Text in Chunks auf."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, text: str, source_file: str) -> list[Chunk]:
        """Fixed-Size Chunking mit Overlap und Satz-Grenzen."""
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Versuche an Satzende zu brechen
            if end < len(text):
                search_start = max(end - int(self.chunk_size * 0.2), start)
                for sep in ['. ', '.\n', '\n\n', '\n', ' ']:
                    last_sep = text.rfind(sep, search_start, end)
                    if last_sep > start:
                        end = last_sep + len(sep)
                        break
            
            chunk_content = text[start:end].strip()
            
            if chunk_content and len(chunk_content) > 20:  # Minimale Chunk-Länge
                file_stem = Path(source_file).stem
                chunks.append(Chunk(
                    id=f"{file_stem}_{chunk_index}",
                    content=chunk_content,
                    source_file=str(source_file),
                    chunk_index=chunk_index,
                    metadata={
                        "source": str(source_file),
                        "chunk_index": chunk_index,
                        "char_start": start,
                        "char_end": end
                    }
                ))
                chunk_index += 1
            
            start = end - self.chunk_overlap if end < len(text) else len(text)
        
        return chunks


# =============================================================================
# Datenbank-Backends für Vektor-Speicherung
# =============================================================================

class VectorStore(ABC):
    """Abstrakte Basis für Vektor-Speicher."""
    
    @abstractmethod
    def connect(self) -> None:
        """Verbindung herstellen."""
        pass
    
    @abstractmethod
    def setup(self, dimensions: int) -> None:
        """Index/Collection erstellen."""
        pass
    
    @abstractmethod
    def store(self, chunks: list[Chunk]) -> float:
        """Chunks speichern. Gibt Zeit in ns zurück."""
        pass
    
    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 5) -> tuple[list[dict], float]:
        """Ähnlichkeitssuche. Gibt Ergebnisse und Zeit in ns zurück."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Daten löschen und Verbindung schließen."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name des Backends."""
        pass


class RedisVectorStore(VectorStore):
    """Redis mit RediSearch für Vektor-Suche."""
    
    def __init__(self, config: dict):
        self.config = config.get("redis", {})
        self.client = None
        self.index_name = "rag_chunks_idx"
        self.prefix = "chunk:"
    
    @property
    def name(self) -> str:
        return "Redis"
    
    def connect(self) -> None:
        self.client = redis.Redis(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 6379),
            decode_responses=False  # Für Binärdaten
        )
        self.client.ping()
    
    def setup(self, dimensions: int) -> None:
        """Erstellt RediSearch Index mit Vektor-Feld."""
        try:
            self.client.execute_command("FT.DROPINDEX", self.index_name, "DD")
        except:
            pass
        
        # RediSearch Index erstellen
        try:
            self.client.execute_command(
                "FT.CREATE", self.index_name,
                "ON", "HASH",
                "PREFIX", "1", self.prefix,
                "SCHEMA",
                "content", "TEXT",
                "source", "TAG",
                "embedding", "VECTOR", "FLAT", "6",
                "TYPE", "FLOAT32",
                "DIM", str(dimensions),
                "DISTANCE_METRIC", "COSINE"
            )
        except Exception as e:
            logger.warning(f"Redis Index-Erstellung: {e}")
    
    def store(self, chunks: list[Chunk]) -> float:
        start = time.perf_counter_ns()
        
        pipe = self.client.pipeline()
        for chunk in chunks:
            if chunk.embedding:
                key = f"{self.prefix}{chunk.id}"
                embedding_bytes = np.array(chunk.embedding, dtype=np.float32).tobytes()
                pipe.hset(key, mapping={
                    "content": chunk.content,
                    "source": chunk.source_file,
                    "embedding": embedding_bytes
                })
        pipe.execute()
        
        return time.perf_counter_ns() - start
    
    def search(self, query_vector: list[float], top_k: int = 5) -> tuple[list[dict], float]:
        start = time.perf_counter_ns()
        
        query_bytes = np.array(query_vector, dtype=np.float32).tobytes()
        
        try:
            results = self.client.execute_command(
                "FT.SEARCH", self.index_name,
                f"*=>[KNN {top_k} @embedding $query_vec AS score]",
                "PARAMS", "2", "query_vec", query_bytes,
                "SORTBY", "score",
                "RETURN", "2", "content", "source",
                "DIALECT", "2"
            )
            
            parsed = []
            if results and len(results) > 1:
                for i in range(1, len(results), 2):
                    if i + 1 < len(results):
                        doc_id = results[i].decode() if isinstance(results[i], bytes) else results[i]
                        fields = results[i + 1]
                        parsed.append({"id": doc_id, "fields": fields})
            
            return parsed, time.perf_counter_ns() - start
        except Exception as e:
            logger.warning(f"Redis Suche fehlgeschlagen: {e}")
            return [], time.perf_counter_ns() - start
    
    def cleanup(self) -> None:
        try:
            self.client.execute_command("FT.DROPINDEX", self.index_name, "DD")
        except:
            pass
        # Alle Chunk-Keys löschen
        keys = self.client.keys(f"{self.prefix}*")
        if keys:
            self.client.delete(*keys)
        self.client.close()


class MongoVectorStore(VectorStore):
    """MongoDB mit Atlas Vector Search (oder lokaler Simulation)."""
    
    def __init__(self, config: dict):
        self.config = config.get("mongodb_vector", config.get("mongodb", {}))
        self.client = None
        self.db = None
        self.collection = None
    
    @property
    def name(self) -> str:
        return "MongoDB"
    
    def connect(self) -> None:
        self.client = pymongo.MongoClient(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 27018),
            serverSelectionTimeoutMS=5000
        )
        self.db = self.client[self.config.get("database", "rag_e2e_test")]
        self.collection = self.db["chunks"]
    
    def setup(self, dimensions: int) -> None:
        """Collection leeren und Index erstellen."""
        self.collection.drop()
        self.collection.create_index([("source", pymongo.ASCENDING)])
        # Für echte Vektor-Suche braucht man Atlas Search Index
        # Hier machen wir Brute-Force Similarity
    
    def store(self, chunks: list[Chunk]) -> float:
        start = time.perf_counter_ns()
        
        documents = []
        for chunk in chunks:
            if chunk.embedding:
                documents.append({
                    "_id": chunk.id,
                    "content": chunk.content,
                    "source": chunk.source_file,
                    "embedding": chunk.embedding,
                    "metadata": chunk.metadata
                })
        
        if documents:
            self.collection.insert_many(documents, ordered=False)
        
        return time.perf_counter_ns() - start
    
    def search(self, query_vector: list[float], top_k: int = 5) -> tuple[list[dict], float]:
        """Brute-Force Cosine Similarity (für lokale Tests ohne Atlas)."""
        start = time.perf_counter_ns()
        
        # Aggregation Pipeline für Ähnlichkeitssuche
        # Ohne Atlas Vector Search machen wir das in Python
        docs = list(self.collection.find({}, {"content": 1, "source": 1, "embedding": 1}))
        
        if not docs:
            return [], time.perf_counter_ns() - start
        
        query_vec = np.array(query_vector)
        results = []
        
        for doc in docs:
            if "embedding" in doc and doc["embedding"]:
                doc_vec = np.array(doc["embedding"])
                similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                results.append({
                    "id": doc["_id"],
                    "content": doc.get("content", "")[:200],
                    "source": doc.get("source", ""),
                    "score": float(similarity)
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k], time.perf_counter_ns() - start
    
    def cleanup(self) -> None:
        self.collection.drop()
        self.client.close()


class PostgresVectorStore(VectorStore):
    """PostgreSQL mit pgvector für echte Vektor-Suche."""
    
    def __init__(self, config: dict):
        self.config = config.get("postgres_pgvector_native", config.get("postgres", {}))
        self.conn = None
        self.dimensions = 384
    
    @property
    def name(self) -> str:
        return "PostgreSQL"
    
    def connect(self) -> None:
        self.conn = psycopg2.connect(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 5433),
            database=self.config.get("database", "rag_vector_test"),
            user=self.config.get("user", "postgres"),
            password=self.config.get("password", "postgres")
        )
        self.conn.autocommit = False
    
    def setup(self, dimensions: int) -> None:
        self.dimensions = dimensions
        cursor = self.conn.cursor()
        
        # pgvector Extension aktivieren
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception as e:
            logger.warning(f"pgvector Extension: {e}")
            self.conn.rollback()
        
        # Tabelle erstellen
        cursor.execute("DROP TABLE IF EXISTS chunks CASCADE;")
        cursor.execute(f"""
            CREATE TABLE chunks (
                id TEXT PRIMARY KEY,
                content TEXT,
                source TEXT,
                embedding vector({dimensions}),
                metadata JSONB
            );
        """)
        
        # HNSW Index für schnelle Suche
        cursor.execute(f"""
            CREATE INDEX ON chunks 
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """)
        
        self.conn.commit()
        cursor.close()
    
    def store(self, chunks: list[Chunk]) -> float:
        start = time.perf_counter_ns()
        
        cursor = self.conn.cursor()
        
        for chunk in chunks:
            if chunk.embedding:
                embedding_str = "[" + ",".join(str(x) for x in chunk.embedding) + "]"
                cursor.execute(
                    """INSERT INTO chunks (id, content, source, embedding, metadata) 
                       VALUES (%s, %s, %s, %s::vector, %s)
                       ON CONFLICT (id) DO NOTHING""",
                    (chunk.id, chunk.content, chunk.source_file, 
                     embedding_str, json.dumps(chunk.metadata))
                )
        
        self.conn.commit()
        cursor.close()
        
        return time.perf_counter_ns() - start
    
    def search(self, query_vector: list[float], top_k: int = 5) -> tuple[list[dict], float]:
        start = time.perf_counter_ns()
        
        cursor = self.conn.cursor()
        
        embedding_str = "[" + ",".join(str(x) for x in query_vector) + "]"
        
        cursor.execute(f"""
            SELECT id, content, source, 
                   1 - (embedding <=> %s::vector) as similarity
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """, (embedding_str, embedding_str, top_k))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1][:200] if row[1] else "",
                "source": row[2],
                "score": float(row[3]) if row[3] else 0.0
            })
        
        cursor.close()
        return results, time.perf_counter_ns() - start
    
    def cleanup(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS chunks CASCADE;")
        self.conn.commit()
        cursor.close()
        self.conn.close()


# =============================================================================
# End-to-End Ingest Performance Test
# =============================================================================

class E2EIngestPerformanceTest(BasePerformanceTest):
    """
    End-to-End Performance-Tests für den kompletten Ingest-Prozess.
    
    WARUM: Nur E2E-Tests zeigen das echte Systemverhalten.
           Alle Komponenten interagieren: Parsing → Chunking → Embedding → DB → Search
    
    HYPOTHESE:
        - PostgreSQL/pgvector hat die beste Such-Qualität
        - MongoDB ist schneller beim Bulk-Insert
        - Redis ist am schnellsten für kleine Datenmengen
    
    REFERENZ: Modul 6, 7, 8 (Chunking, Embeddings, Polyglot Persistence)
    """
    
    @property
    def name(self) -> str:
        return "E2E-Ingest"
    
    @property
    def description(self) -> str:
        return """
    End-to-End Ingest Performance Tests
    
    Testet den KOMPLETTEN RAG-Ingest-Prozess:
    - Datei-Parsing (MD, TXT, JSON, CSV, PDF)
    - Chunking mit Overlap
    - ECHTE Embedding-Generierung (sentence-transformers)
    - Speicherung in Redis, MongoDB, PostgreSQL
    - Vektor-Ähnlichkeitssuche
    
    REFERENZ: Modul 6 (Chunking), Modul 7 (Embeddings), Modul 8 (Polyglot)
        """
    
    def setup(self) -> None:
        """Initialisiert alle Komponenten."""
        ingest_config = self.context.config.get("ingest", {})
        db_config = self.context.config.get("databases", {})
        
        # Ingest-Verzeichnis
        self.ingest_dir = Path(__file__).parent.parent / "ingest"
        if not self.ingest_dir.exists():
            raise FileNotFoundError(f"Ingest-Verzeichnis nicht gefunden: {self.ingest_dir}")
        
        # Dateien sammeln (alle 5 Formate)
        self.files = self._collect_files()
        logger.info(f"Gefunden: {len(self.files)} Dateien zum Verarbeiten")
        
        # Komponenten initialisieren
        self.parser = FileParser()
        self.chunker = Chunker(
            chunk_size=ingest_config.get("chunk_size", 500),
            chunk_overlap=ingest_config.get("chunk_overlap", 50)
        )
        
        # Embedding Generator (echt!)
        model_name = ingest_config.get("embedding_model", "all-MiniLM-L6-v2")
        self.embedding_generator = EmbeddingGenerator(model_name)
        
        # Vector Stores
        self.vector_stores: dict[str, VectorStore] = {}
        
        # Redis
        try:
            redis_store = RedisVectorStore(db_config)
            redis_store.connect()
            self.vector_stores["redis"] = redis_store
            logger.info("✓ Redis verbunden")
        except Exception as e:
            logger.warning(f"Redis nicht verfügbar: {e}")
        
        # MongoDB
        try:
            mongo_store = MongoVectorStore(db_config)
            mongo_store.connect()
            self.vector_stores["mongodb"] = mongo_store
            logger.info("✓ MongoDB verbunden")
        except Exception as e:
            logger.warning(f"MongoDB nicht verfügbar: {e}")
        
        # PostgreSQL
        try:
            pg_store = PostgresVectorStore(db_config)
            pg_store.connect()
            self.vector_stores["postgres"] = pg_store
            logger.info("✓ PostgreSQL verbunden")
        except Exception as e:
            logger.warning(f"PostgreSQL nicht verfügbar: {e}")
        
        if not self.vector_stores:
            raise RuntimeError("Keine Datenbank verfügbar! Starte Docker-Container.")
        
        # Ergebnis-Speicher für Report
        self.e2e_results = {
            "files_processed": 0,
            "total_chunks": 0,
            "embeddings_generated": 0,
            "by_database": {},
            "by_file_type": {}
        }
        
        logger.info(f"✓ E2E-Ingest-Setup abgeschlossen")
        logger.info(f"  Verfügbare DBs: {list(self.vector_stores.keys())}")
        logger.info(f"  Embedding-Dimensionen: {self.embedding_generator.dimensions}")
    
    def _collect_files(self) -> list[Path]:
        """Sammelt alle Dateien (inkl. PDF)."""
        files = []
        supported = {'.md', '.txt', '.json', '.csv', '.pdf'}
        
        for ext in supported:
            found = list(self.ingest_dir.rglob(f"*{ext}"))
            files.extend(found)
            if found:
                logger.info(f"  {ext.upper()}: {len(found)} Dateien")
        
        return sorted(files)
    
    def teardown(self) -> None:
        """Räumt alle Datenbanken auf."""
        for name, store in self.vector_stores.items():
            try:
                store.cleanup()
                logger.info(f"✓ {name} aufgeräumt")
            except Exception as e:
                logger.warning(f"Cleanup {name}: {e}")
        
        logger.info("✓ E2E-Ingest-Test abgeschlossen")
    
    def _run_tests(self) -> None:
        """Führt alle E2E-Tests aus."""
        
        # Phase 1: Ingest (Parse → Chunk → Embed)
        all_chunks = self._test_ingest_pipeline()
        
        if not all_chunks:
            logger.error("Keine Chunks generiert - Tests abgebrochen")
            return
        
        # Phase 2: Store in alle Datenbanken
        self._test_storage(all_chunks)
        
        # Phase 3: Vektor-Suche in allen Datenbanken
        self._test_vector_search(all_chunks)
        
        # Phase 4: Vergleichs-Tests
        self._test_search_comparison(all_chunks)
    
    def _test_ingest_pipeline(self) -> list[Chunk]:
        """
        Test 1: Komplette Ingest-Pipeline (Parse → Chunk → Embed)
        """
        logger.info("=" * 60)
        logger.info("Phase 1: Ingest Pipeline (Parse → Chunk → Embed)")
        logger.info("=" * 60)
        
        all_chunks = []
        parse_times = {}
        chunk_times = {}
        embed_times = {}
        
        for file_path in self.files:
            file_type = file_path.suffix.lower()
            
            # Parse
            parse_start = time.perf_counter_ns()
            text = self.parser.parse(file_path)
            parse_time = time.perf_counter_ns() - parse_start
            
            if not text.strip():
                logger.warning(f"  Leere Datei übersprungen: {file_path.name}")
                continue
            
            # Chunk
            chunk_start = time.perf_counter_ns()
            chunks = self.chunker.chunk(text, str(file_path))
            chunk_time = time.perf_counter_ns() - chunk_start
            
            if not chunks:
                continue
            
            # Embed (Batch für Effizienz)
            embed_start = time.perf_counter_ns()
            texts = [c.content for c in chunks]
            embeddings = self.embedding_generator.generate_batch(texts)
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            embed_time = time.perf_counter_ns() - embed_start
            
            all_chunks.extend(chunks)
            
            # Statistiken pro Dateityp
            if file_type not in parse_times:
                parse_times[file_type] = []
                chunk_times[file_type] = []
                embed_times[file_type] = []
            
            parse_times[file_type].append(parse_time)
            chunk_times[file_type].append(chunk_time)
            embed_times[file_type].append(embed_time)
            
            logger.info(f"  {file_path.name}: {len(chunks)} Chunks")
        
        # Ergebnisse pro Dateityp
        for file_type in parse_times.keys():
            total_parse = sum(parse_times[file_type])
            total_chunk = sum(chunk_times[file_type])
            total_embed = sum(embed_times[file_type])
            num_files = len(parse_times[file_type])
            
            # Parse-Test
            result = self.context.metrics_calculator.calculate(
                test_name=f"E2E Parse {file_type.upper()}",
                database="Ingest",
                operation_type="parse",
                latencies_ms=[ns_to_ms(t) for t in parse_times[file_type]],
                total_operations=num_files,
                notes=f"Parsing von {num_files} {file_type}-Dateien",
                category="E2E/Ingest"
            )
            self.results.append(result)
            
            # Chunk-Test
            result = self.context.metrics_calculator.calculate(
                test_name=f"E2E Chunk {file_type.upper()}",
                database="Ingest",
                operation_type="chunk",
                latencies_ms=[ns_to_ms(t) for t in chunk_times[file_type]],
                total_operations=num_files,
                notes=f"Chunking von {num_files} {file_type}-Dateien",
                category="E2E/Ingest"
            )
            self.results.append(result)
            
            # Embed-Test
            result = self.context.metrics_calculator.calculate(
                test_name=f"E2E Embed {file_type.upper()}",
                database="Ingest",
                operation_type="embed",
                latencies_ms=[ns_to_ms(t) for t in embed_times[file_type]],
                total_operations=num_files,
                notes=f"Embedding von {num_files} {file_type}-Dateien (sentence-transformers)",
                category="E2E/Ingest"
            )
            self.results.append(result)
            
            self.e2e_results["by_file_type"][file_type] = {
                "files": num_files,
                "parse_ms": ns_to_ms(total_parse),
                "chunk_ms": ns_to_ms(total_chunk),
                "embed_ms": ns_to_ms(total_embed)
            }
        
        self.e2e_results["files_processed"] = len(self.files)
        self.e2e_results["total_chunks"] = len(all_chunks)
        self.e2e_results["embeddings_generated"] = len(all_chunks)
        
        logger.info(f"✓ Ingest abgeschlossen: {len(all_chunks)} Chunks generiert")
        
        return all_chunks
    
    def _test_storage(self, chunks: list[Chunk]) -> None:
        """
        Test 2: Speicherung in allen verfügbaren Datenbanken
        """
        logger.info("=" * 60)
        logger.info("Phase 2: Speicherung in Datenbanken")
        logger.info("=" * 60)
        
        for db_name, store in self.vector_stores.items():
            try:
                # Setup (Index/Tabelle erstellen)
                setup_start = time.perf_counter_ns()
                store.setup(self.embedding_generator.dimensions)
                setup_time = time.perf_counter_ns() - setup_start
                
                # Store (Chunks einfügen)
                store_time = store.store(chunks)
                
                total_time = setup_time + store_time
                
                result = self.context.metrics_calculator.calculate(
                    test_name=f"E2E Store {store.name}",
                    database=store.name,
                    operation_type="write",
                    latencies_ms=[ns_to_ms(store_time)],
                    total_operations=len(chunks),
                    notes=f"Bulk-Insert von {len(chunks)} Chunks mit Embeddings",
                    category="E2E/Storage"
                )
                self.results.append(result)
                
                self.e2e_results["by_database"][db_name] = {
                    "setup_ms": ns_to_ms(setup_time),
                    "store_ms": ns_to_ms(store_time),
                    "chunks_stored": len(chunks)
                }
                
                logger.info(f"  {store.name}: {len(chunks)} Chunks in {ns_to_ms(store_time):.1f}ms")
                
            except Exception as e:
                logger.error(f"  {db_name} Speicherung fehlgeschlagen: {e}")
    
    def _test_vector_search(self, chunks: list[Chunk]) -> None:
        """
        Test 3: Vektor-Suche in allen Datenbanken
        """
        logger.info("=" * 60)
        logger.info("Phase 3: Vektor-Ähnlichkeitssuche")
        logger.info("=" * 60)
        
        # Test-Queries generieren
        test_queries = [
            "Was ist Normalisierung in Datenbanken?",
            "Erkläre ACID-Transaktionen",
            "Wie funktioniert ein Index?",
            "Was sind NoSQL-Datenbanken?",
            "Beschreibe das ER-Modell"
        ]
        
        for db_name, store in self.vector_stores.items():
            search_times = []
            total_results = 0
            
            for query in test_queries:
                # Query-Embedding generieren
                query_embedding = self.embedding_generator.generate(query)
                
                # Suche durchführen
                results, search_time = store.search(query_embedding, top_k=5)
                search_times.append(search_time)
                total_results += len(results)
            
            if search_times:
                result = self.context.metrics_calculator.calculate(
                    test_name=f"E2E Search {store.name}",
                    database=store.name,
                    operation_type="vector_search",
                    latencies_ms=[ns_to_ms(t) for t in search_times],
                    total_operations=len(test_queries),
                    notes=f"Top-5 Vektor-Suche mit {len(test_queries)} Queries",
                    category="E2E/Vector Search"
                )
                self.results.append(result)
                
                avg_time = sum(search_times) / len(search_times)
                logger.info(f"  {store.name}: Ø {ns_to_ms(avg_time):.2f}ms pro Suche")
                
                self.e2e_results["by_database"][db_name]["search_avg_ms"] = ns_to_ms(avg_time)
                self.e2e_results["by_database"][db_name]["total_results"] = total_results
    
    def _test_search_comparison(self, chunks: list[Chunk]) -> None:
        """
        Test 4: Direkter Vergleich der Such-Ergebnisse
        """
        logger.info("=" * 60)
        logger.info("Phase 4: Such-Ergebnis-Vergleich")
        logger.info("=" * 60)
        
        # Eine Test-Query für alle DBs
        test_query = "Erkläre Datenbank-Normalisierung und Normalformen"
        query_embedding = self.embedding_generator.generate(test_query)
        
        logger.info(f"Query: \"{test_query}\"")
        logger.info("-" * 60)
        
        for db_name, store in self.vector_stores.items():
            results, search_time = store.search(query_embedding, top_k=3)
            
            logger.info(f"\n{store.name} (in {ns_to_ms(search_time):.2f}ms):")
            for i, res in enumerate(results, 1):
                score = res.get("score", 0)
                content_preview = res.get("content", "")[:80].replace("\n", " ")
                logger.info(f"  {i}. [Score: {score:.4f}] {content_preview}...")
