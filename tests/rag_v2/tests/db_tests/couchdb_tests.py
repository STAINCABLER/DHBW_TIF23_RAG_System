"""
CouchDB Performance Tests
==========================

Performance-Tests für CouchDB als Document Store im RAG-System.

WARUM TESTEN WIR DAS?
---------------------
CouchDB ist ein schemafreier Document Store (Modul 5 & 6):
    - RESTful HTTP API: Einfache Integration
    - MVCC: Multi-Version Concurrency Control
    - MapReduce Views: Flexible Abfragen
    - CouchDB Replication: Multi-Master Sync
    - Mango Queries: MongoDB-ähnliche Abfragen

ERWARTUNGSHALTUNG (HYPOTHESE):
------------------------------
1. Bulk-Inserts (_bulk_docs) sind signifikant schneller
   (Grund: Ein HTTP Request statt N)
   
2. View Queries sind schneller als Mango Queries
   (Grund: Vorberechnete Indizes)
   
3. Document Revisions erhöhen Schreib-Overhead
   
4. P99 Latenz für einzelne GET unter 10ms

REFERENZ:
---------
- Modul 5: Datenmodellierung folgt Access Paths
- Modul 6: Chunking ist Datenmodellierung

Autor: RAG Performance Test Suite
"""

import time
import asyncio
import logging
import json
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    import aiohttp as aiohttp_types

# CouchDB-Treiber
try:
    import couchdb
    HAS_COUCHDB = True
except ImportError:
    HAS_COUCHDB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import ns_to_ms

logger = logging.getLogger(__name__)


class CouchDBPerformanceTest(BasePerformanceTest):
    """
    CouchDB Performance Tests.
    
    Dieser Test deckt folgende Szenarien ab:
    
    WRITE-TESTS (Szenario A):
        - Single Document Insert
        - Bulk Insert (_bulk_docs)
        - Document Update (mit Revision)
        - Conflict Resolution
    
    READ-TESTS (Szenario B):
        - Single Document GET (by ID)
        - Bulk GET (_all_docs)
        - Mango Query (find)
        - View Query (MapReduce)
    
    SPECIAL TESTS:
        - Attachment Operations
        - Changes Feed
    """
    
    DATABASE_NAME = "CouchDB"
    DATABASE_CATEGORY = "NoSQL/Document"
    
    TEST_DESCRIPTION = """
    CouchDB Document Store Performance Tests
    
    WARUM: CouchDB ist ein schemafreier Document Store mit
           RESTful API und eingebauter Replikation.
    
    HYPOTHESE:
        - Bulk Operations sind signifikant schneller
        - View Queries schneller als Mango Queries
        - P99 Latenz für einzelne GET unter 10ms
    
    REFERENZ: Modul 5 & 6 (Chunking & Datenmodellierung)
    """
    
    def __init__(self, context: TestContext):
        """Initialisiert den CouchDB-Test."""
        super().__init__(context)
        
        if not HAS_COUCHDB and not HAS_REQUESTS:
            raise ImportError(
                "CouchDB-Treiber nicht installiert. "
                "Installiere mit: pip install CouchDB oder pip install requests"
            )
        
        # CouchDB-Konfiguration
        db_config = self.config.get("databases", {}).get("couchdb", {})
        self.host = db_config.get("host", "localhost")
        self.port = db_config.get("port", 5984)
        self.database_name = db_config.get("database", "rag_performance_test")
        self.user = db_config.get("user", "admin")
        self.password = db_config.get("password", "admin")
        
        # Base URL
        self.base_url = f"http://{self.user}:{self.password}@{self.host}:{self.port}"
        
        # Clients
        self.server = None
        self.db = None
        self.session = None
        
        # Testdaten
        self.test_chunks: list[dict] = []
        self.inserted_ids: list[str] = []
        self.inserted_revs: dict[str, str] = {}  # ID -> Revision Mapping
    
    def setup(self) -> None:
        """Bereitet den CouchDB-Test vor."""
        logger.info(f"Verbinde zu CouchDB: {self.host}:{self.port}")
        
        if HAS_COUCHDB:
            # CouchDB Python Library
            self.server = couchdb.Server(self.base_url)
            
            # Datenbank erstellen/löschen
            if self.database_name in self.server:
                del self.server[self.database_name]
            self.db = self.server.create(self.database_name)
        else:
            # Fallback: requests
            self.session = requests.Session()
            self.session.auth = (self.user, self.password)
            
            # Datenbank löschen falls vorhanden
            self.session.delete(f"{self.base_url}/{self.database_name}")
            
            # Datenbank erstellen
            response = self.session.put(f"{self.base_url}/{self.database_name}")
            if response.status_code not in (201, 412):
                raise Exception(f"CouchDB Fehler: {response.text}")
        
        logger.info("✓ CouchDB-Verbindung hergestellt")
        
        # Mango Index erstellen
        self._create_indexes()
        
        # Testdaten generieren
        logger.info(f"Generiere {self.num_operations} Chunk-Dokumente...")
        self.test_chunks = list(
            self.data_generator.generate_chunks(self.num_operations)
        )
        logger.info(f"✓ {len(self.test_chunks)} Testdaten generiert")
    
    def _create_indexes(self) -> None:
        """Erstellt Mango-Indizes."""
        index_def = {
            "index": {
                "fields": ["metadata.category"]
            },
            "name": "category-index",
            "type": "json"
        }
        
        if HAS_COUCHDB and self.db:
            # Direkt über HTTP
            import requests
            response = requests.post(
                f"{self.base_url}/{self.database_name}/_index",
                json=index_def,
                headers={"Content-Type": "application/json"}
            )
        elif self.session:
            response = self.session.post(
                f"{self.base_url}/{self.database_name}/_index",
                json=index_def
            )
        
        logger.info("✓ Mango Index erstellt")
    
    def teardown(self) -> None:
        """Räumt nach dem Test auf."""
        try:
            if HAS_COUCHDB and self.server:
                if self.database_name in self.server:
                    del self.server[self.database_name]
            elif self.session:
                self.session.delete(f"{self.base_url}/{self.database_name}")
                self.session.close()
            
            logger.info("✓ CouchDB-Verbindung geschlossen")
        except Exception as e:
            logger.warning(f"Fehler beim Schließen: {e}")
        
        self.test_chunks.clear()
        self.inserted_ids.clear()
        self.inserted_revs.clear()
    
    def warmup(self) -> None:
        """Führt Warmup-Operationen durch."""
        warmup_docs = [
            {"_id": f"warmup_{i}", "data": f"warmup_{i}"}
            for i in range(min(self.warmup_operations, 100))
        ]
        
        if HAS_COUCHDB and self.db:
            # Bulk insert
            self.db.update(warmup_docs)
            
            # Read
            for i in range(10):
                try:
                    doc = self.db[f"warmup_{i}"]
                except:
                    pass
            
            # Delete
            for doc in warmup_docs:
                try:
                    doc_with_rev = self.db[doc["_id"]]
                    self.db.delete(doc_with_rev)
                except:
                    pass
        elif self.session:
            # Bulk insert via HTTP
            self.session.post(
                f"{self.base_url}/{self.database_name}/_bulk_docs",
                json={"docs": warmup_docs}
            )
            
            # Read & Delete
            for i in range(10):
                try:
                    response = self.session.get(
                        f"{self.base_url}/{self.database_name}/warmup_{i}"
                    )
                    if response.ok:
                        doc = response.json()
                        self.session.delete(
                            f"{self.base_url}/{self.database_name}/warmup_{i}?rev={doc['_rev']}"
                        )
                except:
                    pass
    
    def _run_tests(self) -> None:
        """Führt alle CouchDB-Tests aus."""
        
        # =====================================================================
        # WRITE TESTS
        # =====================================================================
        logger.info("\n--- Write Performance Tests ---")
        
        self._test_single_insert()
        self._clear_database()
        
        self._test_bulk_insert()
        
        self._test_document_update()
        
        # =====================================================================
        # READ TESTS
        # =====================================================================
        logger.info("\n--- Read Performance Tests ---")
        
        self._test_single_get()
        self._test_bulk_get()
        self._test_mango_query()
        self._test_all_docs_query()
        
        # =====================================================================
        # ASYNC TESTS
        # =====================================================================
        if HAS_AIOHTTP:
            logger.info("\n--- Async Performance Tests ---")
            asyncio.run(self._run_async_tests())
    
    def _clear_database(self) -> None:
        """Leert die Datenbank."""
        if HAS_COUCHDB and self.server:
            if self.database_name in self.server:
                del self.server[self.database_name]
            self.db = self.server.create(self.database_name)
            self._create_indexes()
        elif self.session:
            self.session.delete(f"{self.base_url}/{self.database_name}")
            self.session.put(f"{self.base_url}/{self.database_name}")
            self._create_indexes()
        
        self.inserted_ids.clear()
        self.inserted_revs.clear()
    
    def _test_single_insert(self) -> None:
        """Test: Einzelne Dokumente einfügen."""
        logger.info("Test: Single Document Insert")
        
        latencies = []
        
        if HAS_COUCHDB and self.db:
            for chunk in self.test_chunks:
                doc = dict(chunk)
                doc["_id"] = chunk["chunk_id"]
                
                start = time.perf_counter_ns()
                doc_id, doc_rev = self.db.save(doc)
                latencies.append(time.perf_counter_ns() - start)
                
                self.inserted_ids.append(doc_id)
                self.inserted_revs[doc_id] = doc_rev
        elif self.session:
            for chunk in self.test_chunks:
                doc = dict(chunk)
                doc_id = chunk["chunk_id"]
                
                start = time.perf_counter_ns()
                response = self.session.put(
                    f"{self.base_url}/{self.database_name}/{doc_id}",
                    json=doc
                )
                latencies.append(time.perf_counter_ns() - start)
                
                if response.ok:
                    result = response.json()
                    self.inserted_ids.append(result["id"])
                    self.inserted_revs[result["id"]] = result["rev"]
        
        result = self.metrics.calculate_from_latencies(
            test_name="CouchDB: Single Document Insert",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_bulk_insert(self) -> None:
        """Test: Bulk Insert mit _bulk_docs."""
        logger.info("Test: Bulk Insert (_bulk_docs)")
        
        # Dokumente vorbereiten
        docs = []
        for chunk in self.test_chunks:
            doc = dict(chunk)
            doc["_id"] = f"bulk_{chunk['chunk_id']}"
            docs.append(doc)
        
        # In Batches aufteilen
        batch_size = self.batch_size
        batches = [docs[i:i+batch_size] for i in range(0, len(docs), batch_size)]
        
        latencies = []
        
        if HAS_COUCHDB and self.db:
            for batch in batches:
                start = time.perf_counter_ns()
                results = self.db.update(batch)
                batch_time = time.perf_counter_ns() - start
                
                # Pro Dokument aufteilen
                per_doc_time = batch_time // len(batch)
                latencies.extend([per_doc_time] * len(batch))
                
                for success, doc_id, rev_or_exc in results:
                    if success:
                        self.inserted_ids.append(doc_id)
                        self.inserted_revs[doc_id] = rev_or_exc
        elif self.session:
            for batch in batches:
                start = time.perf_counter_ns()
                response = self.session.post(
                    f"{self.base_url}/{self.database_name}/_bulk_docs",
                    json={"docs": batch}
                )
                batch_time = time.perf_counter_ns() - start
                
                per_doc_time = batch_time // len(batch)
                latencies.extend([per_doc_time] * len(batch))
                
                if response.ok:
                    for result in response.json():
                        if result.get("ok"):
                            self.inserted_ids.append(result["id"])
                            self.inserted_revs[result["id"]] = result["rev"]
        
        result = self.metrics.calculate_from_latencies(
            test_name="CouchDB: Bulk Insert (_bulk_docs)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_document_update(self) -> None:
        """Test: Dokument-Updates mit Revision.
        
        HINWEIS: Misst nur die PUT-Operation, nicht das vorherige GET.
        Das GET ist ein separater Overhead, der in der Praxis
        durch Caching optimiert werden kann.
        """
        logger.info("Test: Document Update (nur PUT, ohne GET)")
        
        latencies = []
        
        # Erste 1000 Dokumente updaten
        ids_to_update = self.inserted_ids[:min(1000, len(self.inserted_ids))]
        
        if HAS_COUCHDB and self.db:
            for doc_id in ids_to_update:
                # GET außerhalb der Zeitmessung (konsistent mit session-Branch)
                doc = self.db[doc_id]
                doc["updated"] = True
                doc["update_count"] = doc.get("update_count", 0) + 1
                
                # Nur PUT messen
                start = time.perf_counter_ns()
                doc_id, doc_rev = self.db.save(doc)
                latencies.append(time.perf_counter_ns() - start)
                
                self.inserted_revs[doc_id] = doc_rev
        elif self.session:
            for doc_id in ids_to_update:
                # Erst Dokument holen (außerhalb Zeitmessung)
                response = self.session.get(
                    f"{self.base_url}/{self.database_name}/{doc_id}"
                )
                
                if response.ok:
                    doc = response.json()
                    doc["updated"] = True
                    doc["update_count"] = doc.get("update_count", 0) + 1
                    
                    # Nur PUT messen
                    start = time.perf_counter_ns()
                    response = self.session.put(
                        f"{self.base_url}/{self.database_name}/{doc_id}",
                        json=doc
                    )
                    latencies.append(time.perf_counter_ns() - start)
                    
                    if response.ok:
                        self.inserted_revs[doc_id] = response.json()["rev"]
        
        result = self.metrics.calculate_from_latencies(
            test_name="CouchDB: Document Update (mit Revision)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_single_get(self) -> None:
        """Test: Einzelnes Dokument abrufen."""
        logger.info("Test: Single Document GET")
        
        latencies = []
        
        if HAS_COUCHDB and self.db:
            for doc_id in self.inserted_ids[:self.num_operations]:
                start = time.perf_counter_ns()
                doc = self.db[doc_id]
                latencies.append(time.perf_counter_ns() - start)
        elif self.session:
            for doc_id in self.inserted_ids[:self.num_operations]:
                start = time.perf_counter_ns()
                response = self.session.get(
                    f"{self.base_url}/{self.database_name}/{doc_id}"
                )
                latencies.append(time.perf_counter_ns() - start)
        
        result = self.metrics.calculate_from_latencies(
            test_name="CouchDB: Single Document GET",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_bulk_get(self) -> None:
        """Test: Bulk GET mit _all_docs."""
        logger.info("Test: Bulk GET (_all_docs mit keys)")
        
        latencies = []
        batch_size = 100
        
        for i in range(0, min(1000, len(self.inserted_ids)), batch_size):
            keys = self.inserted_ids[i:i+batch_size]
            
            if HAS_COUCHDB and self.db:
                start = time.perf_counter_ns()
                # Verwendung von view
                result = self.db.view('_all_docs', keys=keys, include_docs=True)
                list(result)  # Materialisieren
                batch_time = time.perf_counter_ns() - start
            elif self.session:
                start = time.perf_counter_ns()
                response = self.session.post(
                    f"{self.base_url}/{self.database_name}/_all_docs?include_docs=true",
                    json={"keys": keys}
                )
                batch_time = time.perf_counter_ns() - start
            
            per_doc_time = batch_time // len(keys)
            latencies.extend([per_doc_time] * len(keys))
        
        result = self.metrics.calculate_from_latencies(
            test_name="CouchDB: Bulk GET (_all_docs mit keys)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_mango_query(self) -> None:
        """Test: Mango Query (find)."""
        logger.info("Test: Mango Query (find)")
        
        latencies = []
        categories = ["category_a", "category_b", "category_c"]
        
        for i in range(min(500, self.num_operations)):
            category = categories[i % len(categories)]
            
            query = {
                "selector": {
                    "metadata.category": category
                },
                "limit": 10
            }
            
            if self.session:
                start = time.perf_counter_ns()
                response = self.session.post(
                    f"{self.base_url}/{self.database_name}/_find",
                    json=query
                )
                latencies.append(time.perf_counter_ns() - start)
            elif HAS_COUCHDB and self.db:
                start = time.perf_counter_ns()
                # Mango query via HTTP
                import requests
                response = requests.post(
                    f"{self.base_url}/{self.database_name}/_find",
                    json=query
                )
                latencies.append(time.perf_counter_ns() - start)
        
        result = self.metrics.calculate_from_latencies(
            test_name="CouchDB: Mango Query (find)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_all_docs_query(self) -> None:
        """Test: _all_docs Query mit Pagination."""
        logger.info("Test: _all_docs Query (Pagination)")
        
        latencies = []
        
        for i in range(100):
            skip = i * 100
            
            if self.session:
                start = time.perf_counter_ns()
                response = self.session.get(
                    f"{self.base_url}/{self.database_name}/_all_docs",
                    params={"limit": 100, "skip": skip, "include_docs": "true"}
                )
                latencies.append(time.perf_counter_ns() - start)
            elif HAS_COUCHDB and self.db:
                start = time.perf_counter_ns()
                result = self.db.view('_all_docs', limit=100, skip=skip, include_docs=True)
                list(result)
                latencies.append(time.perf_counter_ns() - start)
        
        result = self.metrics.calculate_from_latencies(
            test_name="CouchDB: _all_docs Query (Pagination)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    async def _run_async_tests(self) -> None:
        """Führt asynchrone Tests aus."""
        logger.info("Starte asynchrone CouchDB-Tests...")
        
        async with aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self.user, self.password)
        ) as session:
            await self._async_concurrent_reads(session)
            await self._async_concurrent_writes(session)
    
    async def _async_concurrent_reads(self, session: Any) -> None:
        """Test: Parallele asynchrone Lesevorgänge."""
        logger.info(f"Test: Async Concurrent Reads ({self.concurrent_clients} Clients)")
        
        base_url = f"http://{self.host}:{self.port}/{self.database_name}"
        
        async def single_read(doc_id: str) -> int:
            start = time.perf_counter_ns()
            async with session.get(f"{base_url}/{doc_id}") as response:
                await response.json()
            return time.perf_counter_ns() - start
        
        tasks = [
            single_read(self.inserted_ids[i % len(self.inserted_ids)])
            for i in range(min(1000, self.num_operations))
        ]
        
        latencies = await asyncio.gather(*tasks)
        
        result = self.metrics.calculate_from_latencies(
            test_name=f"CouchDB: Async Concurrent Reads ({self.concurrent_clients} Clients)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=list(latencies),
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    async def _async_concurrent_writes(self, session: Any) -> None:
        """Test: Parallele asynchrone Schreibvorgänge."""
        logger.info(f"Test: Async Concurrent Writes ({self.concurrent_clients} Clients)")
        
        base_url = f"http://{self.host}:{self.port}/{self.database_name}"
        
        async def single_write(i: int) -> int:
            doc = {
                "_id": f"async_{i}",
                "data": f"async_data_{i}",
                "type": "async_test"
            }
            
            start = time.perf_counter_ns()
            async with session.put(f"{base_url}/async_{i}", json=doc) as response:
                await response.json()
            return time.perf_counter_ns() - start
        
        tasks = [single_write(i) for i in range(min(1000, self.num_operations))]
        latencies = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Nur erfolgreiche Latencies
        valid_latencies = [l for l in latencies if isinstance(l, int)]
        
        result = self.metrics.calculate_from_latencies(
            test_name=f"CouchDB: Async Concurrent Writes ({self.concurrent_clients} Clients)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=valid_latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
