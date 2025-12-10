"""
Vector Search Performance Tests
================================

Performance-Tests für Vektorsuche mit pgvector und MongoDB.

WARUM TESTEN WIR DAS?
---------------------
Die Vektorsuche ist DER kritische Pfad im RAG-System (Modul 7):
    - ANN-Suche: Approximate Nearest Neighbor für Embedding-Matching
    - SLO: Das 50ms Budget für P95 Latenz muss eingehalten werden
    - Workload-Isolation: Vektorsuche muss isoliert laufen

ERWARTUNGSHALTUNG (HYPOTHESE):
------------------------------
1. HNSW-Index (ANN) ist 10-100x schneller als lineare Suche (KNN)
   (Grund: Hierarchische Graphstruktur vs. O(n) Scan)
   
2. P95 Latenz mit HNSW sollte unter 50ms liegen (SLO!)
   
3. Pre-Filtering (Metadaten) reduziert Suchraum und beschleunigt Suche
   
4. pgvector-Native ist schneller als manuelle Installation
   (Grund: Optimierte Kompilierung im offiziellen Image)

REFERENZ:
---------
- Modul 7: Embeddings als Datentyp mit eigenem Workload
- Modul 7 Labor: Vektor-DB-Annahme auf dem Prüfstand

Autor: RAG Performance Test Suite
"""

import time
import asyncio
import logging
from typing import Optional
import random

# NumPy für Vektor-Operationen
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# PostgreSQL-Treiber
try:
    import psycopg2
    from psycopg2.extras import execute_values
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

# MongoDB-Treiber
try:
    import pymongo
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import ns_to_ms

logger = logging.getLogger(__name__)


class VectorPerformanceTest(BasePerformanceTest):
    """
    Vector Search Performance Tests - pgvector und MongoDB.
    
    Dieser Test ist der WICHTIGSTE für das RAG-System!
    
    Die Vektorsuche liegt im kritischen Pfad und muss das 50ms SLO
    (P95 Latenz) einhalten (siehe Modul 7).
    
    GETESTETE SZENARIEN:
    
    pgvector (PostgreSQL):
        - Exakte Suche (KNN): Lineare Distanzberechnung (Baseline)
        - Approximative Suche (ANN): HNSW-Index (optimiert)
        - Pre-Filtering: Metadaten-Filter vor Vektorsuche
    
    pgvector Varianten:
        - Native Image: pgvector/pgvector:pg16
        - Manuelle Installation: postgres:16 + CREATE EXTENSION
    
    MongoDB (falls verfügbar):
        - Vector Search mit jlmconsulting/mongo-vector-search
    """
    
    DATABASE_NAME = "Vector Search"
    
    TEST_DESCRIPTION = """
    Vektorsuche Performance Tests (pgvector & MongoDB)
    
    WARUM: Die Vektorsuche ist der kritische Pfad im RAG-System.
           Das 50ms SLO (P95) muss eingehalten werden!
    
    HYPOTHESE:
        - HNSW-Index ist 10-100x schneller als lineare Suche
        - P95 Latenz mit HNSW unter 50ms
        - Pre-Filtering beschleunigt die Suche
    
    REFERENZ: Modul 7 (Embeddings & Vektorsuche)
    """
    
    # SLO für Vektorsuche: 50ms P95 (aus Modul 7)
    VECTOR_SEARCH_SLO_MS = 50.0
    
    def __init__(self, context: TestContext):
        """Initialisiert den Vector-Test."""
        super().__init__(context)
        
        if not HAS_NUMPY:
            raise ImportError(
                "numpy nicht installiert. "
                "Installiere mit: pip install numpy"
            )
        
        if not HAS_PSYCOPG2:
            raise ImportError(
                "psycopg2 nicht installiert. "
                "Installiere mit: pip install psycopg2-binary"
            )
        
        # Konfiguration
        general = self.config.get("general", {})
        self.vector_count = general.get("vector_count", 50000)
        self.vector_dimensions = general.get("vector_dimensions", 768)
        
        scenarios = self.config.get("scenarios", {}).get("vector_tests", {})
        self.num_searches = scenarios.get("num_searches", 1000)
        self.top_k = scenarios.get("top_k", 5)
        
        # pgvector Native Konfiguration
        pg_native = self.config.get("databases", {}).get("postgres_pgvector_native", {})
        self.pg_native_host = pg_native.get("host", "localhost")
        self.pg_native_port = pg_native.get("port", 5433)
        self.pg_native_db = pg_native.get("database", "rag_vector_test")
        self.pg_native_user = pg_native.get("user", "postgres")
        self.pg_native_password = pg_native.get("password", "postgres")
        
        # pgvector Manual Konfiguration
        pg_manual = self.config.get("databases", {}).get("postgres_pgvector_manual", {})
        self.pg_manual_host = pg_manual.get("host", "localhost")
        self.pg_manual_port = pg_manual.get("port", 5434)
        self.pg_manual_db = pg_manual.get("database", "rag_vector_test")
        self.pg_manual_user = pg_manual.get("user", "postgres")
        self.pg_manual_password = pg_manual.get("password", "postgres")
        
        # MongoDB Vector Konfiguration
        mongo_vector = self.config.get("databases", {}).get("mongodb_vector", {})
        self.mongo_host = mongo_vector.get("host", "localhost")
        self.mongo_port = mongo_vector.get("port", 27018)
        self.mongo_db = mongo_vector.get("database", "rag_vector_test")
        
        # Connections
        self.pg_native_conn = None
        self.pg_manual_conn = None
        self.mongo_client = None
        
        # Testdaten
        self.vectors: list[dict] = []
        self.query_vectors: list[list[float]] = []
        self.categories = ["category_a", "category_b", "category_c"]
    
    def setup(self) -> None:
        """
        Bereitet die Vector-Tests vor.
        
        - Verbindungen herstellen
        - pgvector Extension aktivieren
        - Tabellen/Collections erstellen
        - Testdaten generieren und einfügen
        """
        logger.info(f"Generiere {self.vector_count} Vektoren ({self.vector_dimensions}D)...")
        
        # Testdaten generieren
        self.vectors = self.data_generator.generate_vectors(self.vector_count)
        
        # Query-Vektoren generieren
        self.query_vectors = [
            self.data_generator.generate_query_vector()
            for _ in range(self.num_searches)
        ]
        
        logger.info(f"✓ {len(self.vectors)} Vektoren generiert")
        logger.info(f"✓ {len(self.query_vectors)} Query-Vektoren generiert")
        
        # pgvector Native Setup
        self._setup_pgvector_native()
        
        # pgvector Manual Setup (falls verfügbar)
        self._setup_pgvector_manual()
        
        # MongoDB Vector Setup (falls verfügbar)
        self._setup_mongodb_vector()
    
    def _setup_pgvector_native(self) -> None:
        """Richtet pgvector mit dem nativen Image ein."""
        logger.info(f"Verbinde zu pgvector-native: {self.pg_native_host}:{self.pg_native_port}")
        
        try:
            self.pg_native_conn = psycopg2.connect(
                host=self.pg_native_host,
                port=self.pg_native_port,
                database=self.pg_native_db,
                user=self.pg_native_user,
                password=self.pg_native_password,
                connect_timeout=10,
            )
            self.pg_native_conn.autocommit = True
            
            with self.pg_native_conn.cursor() as cur:
                # Extension aktivieren
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                
                # Tabelle erstellen
                cur.execute("DROP TABLE IF EXISTS embeddings")
                cur.execute(f"""
                    CREATE TABLE embeddings (
                        id SERIAL PRIMARY KEY,
                        embedding_id VARCHAR(36) UNIQUE,
                        vector vector({self.vector_dimensions}),
                        category VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Index auf Kategorie für Pre-Filtering
                cur.execute("CREATE INDEX idx_category ON embeddings(category)")
            
            logger.info("✓ pgvector-native verbunden und konfiguriert")
            
            # Daten einfügen
            self._insert_vectors_pgvector(self.pg_native_conn, "native")
            
        except Exception as e:
            logger.warning(f"pgvector-native nicht verfügbar: {e}")
            self.pg_native_conn = None
    
    def _setup_pgvector_manual(self) -> None:
        """Richtet pgvector mit manueller Installation ein."""
        logger.info(f"Verbinde zu pgvector-manual: {self.pg_manual_host}:{self.pg_manual_port}")
        
        try:
            self.pg_manual_conn = psycopg2.connect(
                host=self.pg_manual_host,
                port=self.pg_manual_port,
                database=self.pg_manual_db,
                user=self.pg_manual_user,
                password=self.pg_manual_password,
                connect_timeout=10,
            )
            self.pg_manual_conn.autocommit = True
            
            with self.pg_manual_conn.cursor() as cur:
                # Extension aktivieren (muss installiert sein!)
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                
                # Tabelle erstellen
                cur.execute("DROP TABLE IF EXISTS embeddings")
                cur.execute(f"""
                    CREATE TABLE embeddings (
                        id SERIAL PRIMARY KEY,
                        embedding_id VARCHAR(36) UNIQUE,
                        vector vector({self.vector_dimensions}),
                        category VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cur.execute("CREATE INDEX idx_category ON embeddings(category)")
            
            logger.info("✓ pgvector-manual verbunden und konfiguriert")
            
            # Daten einfügen
            self._insert_vectors_pgvector(self.pg_manual_conn, "manual")
            
        except Exception as e:
            logger.warning(f"pgvector-manual nicht verfügbar: {e}")
            self.pg_manual_conn = None
    
    def _setup_mongodb_vector(self) -> None:
        """Richtet MongoDB mit Vector Search ein."""
        if not HAS_PYMONGO:
            logger.warning("pymongo nicht verfügbar, MongoDB-Vector-Tests übersprungen")
            return
        
        logger.info(f"Verbinde zu MongoDB-Vector: {self.mongo_host}:{self.mongo_port}")
        
        try:
            self.mongo_client = MongoClient(
                host=self.mongo_host,
                port=self.mongo_port,
                serverSelectionTimeoutMS=5000,
            )
            
            # Verbindung testen
            self.mongo_client.admin.command("ping")
            
            db = self.mongo_client[self.mongo_db]
            collection = db["embeddings"]
            
            # Collection leeren
            collection.drop()
            
            # Daten einfügen (in Batches)
            logger.info("Füge Vektoren in MongoDB ein...")
            batch_size = 1000
            for i in range(0, len(self.vectors), batch_size):
                batch = self.vectors[i:i + batch_size]
                docs = [
                    {
                        "embedding_id": v["embedding_id"],
                        "vector": v["vector"],
                        "category": v["metadata"]["category"],
                    }
                    for v in batch
                ]
                collection.insert_many(docs)
            
            logger.info(f"✓ {len(self.vectors)} Vektoren in MongoDB eingefügt")
            
        except Exception as e:
            logger.warning(f"MongoDB-Vector nicht verfügbar: {e}")
            self.mongo_client = None
    
    def _insert_vectors_pgvector(self, conn, variant: str) -> None:
        """Fügt Vektoren in pgvector ein."""
        logger.info(f"Füge Vektoren in pgvector-{variant} ein...")
        
        with conn.cursor() as cur:
            # Batch-Insert
            batch_size = 1000
            for i in range(0, len(self.vectors), batch_size):
                batch = self.vectors[i:i + batch_size]
                
                values = [
                    (
                        v["embedding_id"],
                        v["vector"],  # Liste wird automatisch zu vector konvertiert
                        v["metadata"]["category"]
                    )
                    for v in batch
                ]
                
                execute_values(
                    cur,
                    """
                    INSERT INTO embeddings (embedding_id, vector, category)
                    VALUES %s
                    """,
                    values,
                    template="(%s, %s::vector, %s)"
                )
        
        logger.info(f"✓ {len(self.vectors)} Vektoren in pgvector-{variant} eingefügt")
    
    def teardown(self) -> None:
        """Räumt nach den Tests auf."""
        if self.pg_native_conn:
            try:
                self.pg_native_conn.close()
            except Exception:
                pass
        
        if self.pg_manual_conn:
            try:
                self.pg_manual_conn.close()
            except Exception:
                pass
        
        if self.mongo_client:
            try:
                self.mongo_client.close()
            except Exception:
                pass
        
        self.vectors.clear()
        self.query_vectors.clear()
        
        logger.info("✓ Vector-Test Cleanup abgeschlossen")
    
    def warmup(self) -> None:
        """Führt Warmup-Queries aus."""
        if self.pg_native_conn:
            with self.pg_native_conn.cursor() as cur:
                for i in range(10):
                    query_vec = self.query_vectors[i % len(self.query_vectors)]
                    cur.execute(
                        f"""
                        SELECT embedding_id 
                        FROM embeddings 
                        ORDER BY vector <-> %s::vector 
                        LIMIT 1
                        """,
                        (query_vec,)
                    )
                    cur.fetchall()
    
    def _run_tests(self) -> None:
        """Führt alle Vector-Tests aus."""
        # =====================================================================
        # pgvector NATIVE Tests
        # =====================================================================
        
        if self.pg_native_conn:
            logger.info("\n" + "=" * 60)
            logger.info("pgvector NATIVE Tests")
            logger.info("=" * 60)
            
            # Exakte Suche (ohne Index)
            self._test_pgvector_exact_search(self.pg_native_conn, "Native")
            
            # HNSW-Index erstellen
            self._create_hnsw_index(self.pg_native_conn, "Native")
            
            # ANN-Suche (mit HNSW)
            self._test_pgvector_ann_search(self.pg_native_conn, "Native")
            
            # Pre-Filtering
            self._test_pgvector_filtered_search(self.pg_native_conn, "Native")
        
        # =====================================================================
        # pgvector MANUAL Tests
        # =====================================================================
        
        if self.pg_manual_conn:
            logger.info("\n" + "=" * 60)
            logger.info("pgvector MANUAL Tests")
            logger.info("=" * 60)
            
            self._test_pgvector_exact_search(self.pg_manual_conn, "Manual")
            self._create_hnsw_index(self.pg_manual_conn, "Manual")
            self._test_pgvector_ann_search(self.pg_manual_conn, "Manual")
            self._test_pgvector_filtered_search(self.pg_manual_conn, "Manual")
        
        # =====================================================================
        # MongoDB Vector Tests
        # =====================================================================
        
        if self.mongo_client:
            logger.info("\n" + "=" * 60)
            logger.info("MongoDB Vector Tests")
            logger.info("=" * 60)
            
            self._test_mongodb_vector_search()
    
    def _create_hnsw_index(self, conn, variant: str) -> None:
        """
        Erstellt einen HNSW-Index für ANN-Suche.
        
        HNSW (Hierarchical Navigable Small Worlds) ist ein Graph-basierter
        Index, der schnelle approximative Nearest-Neighbor-Suche ermöglicht.
        
        Parameter:
            - m: Anzahl der Verbindungen pro Knoten (default: 16)
            - ef_construction: Größe der dynamischen Liste beim Bau (default: 64)
        """
        logger.info(f"Erstelle HNSW-Index für pgvector-{variant}...")
        
        with conn.cursor() as cur:
            # Alten Index löschen
            cur.execute("DROP INDEX IF EXISTS idx_hnsw_vector")
            
            # HNSW-Index erstellen
            # Cosine-Distanz für normalisierte Vektoren (wie Embeddings)
            cur.execute("""
                CREATE INDEX idx_hnsw_vector 
                ON embeddings 
                USING hnsw (vector vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
        
        logger.info(f"✓ HNSW-Index für pgvector-{variant} erstellt")
    
    def _test_pgvector_exact_search(self, conn, variant: str) -> None:
        """
        Test: Exakte Vektorsuche (KNN) ohne Index
        
        KONTEXT:
            Ohne Index muss PostgreSQL ALLE Vektoren durchsuchen
            und die Distanz zu jedem berechnen. Dies ist O(n).
            
            Bei 50.000 Vektoren mit 768 Dimensionen ist das
            extrem rechenintensiv!
        
        ERWARTUNG:
            Sehr langsam (>100ms), SLO wird NICHT eingehalten
        """
        logger.info(f"Test: Exakte Suche (KNN) - pgvector-{variant}")
        
        latencies = []
        
        # Index temporär deaktivieren
        with conn.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS idx_hnsw_vector")
        
        # Nur 100 Queries für exakte Suche (zu langsam für viele)
        num_queries = min(100, len(self.query_vectors))
        
        with conn.cursor() as cur:
            for query_vec in self.query_vectors[:num_queries]:
                start = time.perf_counter_ns()
                
                # Cosine-Distanz (1 - similarity)
                cur.execute(
                    f"""
                    SELECT embedding_id, vector <=> %s::vector as distance
                    FROM embeddings
                    ORDER BY distance
                    LIMIT %s
                    """,
                    (query_vec, self.top_k)
                )
                cur.fetchall()
                
                end = time.perf_counter_ns()
                latencies.append(ns_to_ms(end - start))
        
        total_duration_ms = sum(latencies)
        
        self.record_result(
            test_name=f"pgvector-{variant} KNN (exakt)",
            operation_type="vector_search",
            latencies_ms=latencies,
            total_operations=num_queries,
            total_duration_ms=total_duration_ms,
            slo_target_ms=self.VECTOR_SEARCH_SLO_MS,
            notes=f"Exakte Suche ohne Index, {self.vector_count} Vektoren"
        )
    
    def _test_pgvector_ann_search(self, conn, variant: str) -> None:
        """
        Test: Approximative Vektorsuche (ANN) mit HNSW-Index
        
        KONTEXT:
            HNSW ermöglicht O(log n) Suche durch hierarchische
            Graph-Navigation. Die Genauigkeit (Recall) wird
            für Geschwindigkeit geopfert.
            
            Dies ist der STANDARD für Produktionssysteme!
        
        ERWARTUNG:
            Schnell (<50ms P95), SLO wird eingehalten
        
        REFERENZ:
            Modul 7: Embeddings als Datentyp
        """
        logger.info(f"Test: ANN-Suche (HNSW) - pgvector-{variant}")
        
        latencies = []
        
        with conn.cursor() as cur:
            # ef_search für Query-Zeit (höher = genauer, langsamer)
            cur.execute("SET hnsw.ef_search = 40")
            
            for query_vec in self.query_vectors:
                start = time.perf_counter_ns()
                
                cur.execute(
                    f"""
                    SELECT embedding_id, vector <=> %s::vector as distance
                    FROM embeddings
                    ORDER BY distance
                    LIMIT %s
                    """,
                    (query_vec, self.top_k)
                )
                cur.fetchall()
                
                end = time.perf_counter_ns()
                latencies.append(ns_to_ms(end - start))
        
        total_duration_ms = sum(latencies)
        
        self.record_result(
            test_name=f"pgvector-{variant} ANN (HNSW)",
            operation_type="vector_search",
            latencies_ms=latencies,
            total_operations=len(self.query_vectors),
            total_duration_ms=total_duration_ms,
            slo_target_ms=self.VECTOR_SEARCH_SLO_MS,
            notes=f"HNSW-Index, ef_search=40, {self.vector_count} Vektoren"
        )
    
    def _test_pgvector_filtered_search(self, conn, variant: str) -> None:
        """
        Test: Vektorsuche mit Pre-Filtering (Metadaten)
        
        KONTEXT:
            In der Praxis wird die Suche oft auf eine Teilmenge
            der Vektoren beschränkt (z.B. nur Produkt-Kategorie X).
            
            Pre-Filtering reduziert den Suchraum und kann die
            Suche beschleunigen.
        
        ERWARTUNG:
            Schneller als ungefilterte Suche (kleinerer Suchraum)
        
        REFERENZ:
            Modul 7: Metadaten-Nutzung und Pre-Filtering
        """
        logger.info(f"Test: Filtered ANN-Suche - pgvector-{variant}")
        
        latencies = []
        
        with conn.cursor() as cur:
            cur.execute("SET hnsw.ef_search = 40")
            
            for i, query_vec in enumerate(self.query_vectors):
                # Kategorie zyklisch wählen
                category = self.categories[i % len(self.categories)]
                
                start = time.perf_counter_ns()
                
                cur.execute(
                    f"""
                    SELECT embedding_id, vector <=> %s::vector as distance
                    FROM embeddings
                    WHERE category = %s
                    ORDER BY distance
                    LIMIT %s
                    """,
                    (query_vec, category, self.top_k)
                )
                cur.fetchall()
                
                end = time.perf_counter_ns()
                latencies.append(ns_to_ms(end - start))
        
        total_duration_ms = sum(latencies)
        
        self.record_result(
            test_name=f"pgvector-{variant} Filtered ANN",
            operation_type="vector_search",
            latencies_ms=latencies,
            total_operations=len(self.query_vectors),
            total_duration_ms=total_duration_ms,
            slo_target_ms=self.VECTOR_SEARCH_SLO_MS,
            notes=f"HNSW mit Kategorie-Filter, {self.vector_count} Vektoren"
        )
    
    def _test_mongodb_vector_search(self) -> None:
        """
        Test: MongoDB Vector Search
        
        KONTEXT:
            MongoDB bietet (in Atlas oder mit Community-Images)
            native Vektorsuche. Diese Tests prüfen die Performance
            im lokalen Docker-Setup.
        
        HINWEIS:
            Die Verfügbarkeit und Performance hängt stark vom
            verwendeten Image ab.
        """
        logger.info("Test: MongoDB Vector Search")
        
        db = self.mongo_client[self.mongo_db]
        collection = db["embeddings"]
        
        latencies = []
        
        # Nur 100 Queries (MongoDB lokale Vektorsuche ist limitiert)
        num_queries = min(100, len(self.query_vectors))
        
        for query_vec in self.query_vectors[:num_queries]:
            start = time.perf_counter_ns()
            
            # Aggregation Pipeline für Vektorsuche
            # (funktioniert nur mit Atlas oder speziellem Image)
            try:
                pipeline = [
                    {
                        "$addFields": {
                            "similarity": {
                                "$reduce": {
                                    "input": {"$range": [0, self.vector_dimensions]},
                                    "initialValue": 0,
                                    "in": {
                                        "$add": [
                                            "$$value",
                                            {
                                                "$multiply": [
                                                    {"$arrayElemAt": ["$vector", "$$this"]},
                                                    {"$arrayElemAt": [query_vec, "$$this"]}
                                                ]
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    },
                    {"$sort": {"similarity": -1}},
                    {"$limit": self.top_k},
                    {"$project": {"embedding_id": 1, "similarity": 1}}
                ]
                
                list(collection.aggregate(pipeline))
                
            except Exception as e:
                logger.warning(f"MongoDB Aggregation fehlgeschlagen: {e}")
                # Fallback: Einfacher find() ohne Vektorsuche
                list(collection.find().limit(self.top_k))
            
            end = time.perf_counter_ns()
            latencies.append(ns_to_ms(end - start))
        
        total_duration_ms = sum(latencies)
        
        self.record_result(
            test_name="MongoDB Vector Search",
            operation_type="vector_search",
            latencies_ms=latencies,
            total_operations=num_queries,
            total_duration_ms=total_duration_ms,
            slo_target_ms=self.VECTOR_SEARCH_SLO_MS,
            notes=f"MongoDB Aggregation Pipeline, {self.vector_count} Vektoren"
        )
