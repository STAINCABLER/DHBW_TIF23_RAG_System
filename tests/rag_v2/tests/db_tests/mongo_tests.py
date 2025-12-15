"""
MongoDB Performance Tests
==========================

Performance-Tests für MongoDB als Document Store im RAG-System.

WARUM TESTEN WIR DAS?
---------------------
MongoDB ist der primäre Speicher für Chunk-Dokumente im RAG-System (Modul 5 & 6):
    - Chunk-Speicherung: Text + Metadaten als JSON-Dokumente
    - Flexible Schema: Unterschiedliche Chunk-Strukturen möglich
    - Schneller Abruf: Chunks nach ID laden (nach Vektorsuche)

ERWARTUNGSHALTUNG (HYPOTHESE):
------------------------------
1. insert_many() ist 5-10x schneller als einzelne insert_one()
   (Grund: Reduzierung von Netzwerk-Roundtrips und Batch-Optimierung)
   
2. find_one() ist schneller als find() mit Limit 1
   (Grund: Optimierter Code-Pfad für Einzeldokument-Abruf)
   
3. $in-Query für mehrere IDs ist effizienter als mehrere find_one()
   (Grund: Ein Netzwerk-Roundtrip statt N)

REFERENZ:
---------
- Modul 5: Datenmodellierung folgt Access Paths
- Modul 6: Chunking ist Datenmodellierung
- Modul 8: Performance-Myth-Busting (MongoDB Bulk-Insert)

Autor: RAG Performance Test Suite
"""

import time
import asyncio
import logging
from typing import Optional

# MongoDB-Treiber
try:
    import pymongo
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    HAS_PYMONGO = False

try:
    import motor.motor_asyncio
    HAS_MOTOR = True
except ImportError:
    HAS_MOTOR = False

from bson import ObjectId

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import ns_to_ms

logger = logging.getLogger(__name__)


class MongoPerformanceTest(BasePerformanceTest):
    """
    MongoDB Performance Tests - Synchron und Asynchron.
    
    Dieser Test deckt folgende Szenarien ab:
    
    WRITE-TESTS (Szenario A):
        - Single Inserts: Einzelne insert_one() Operationen (Baseline)
        - Bulk Inserts: insert_many() für Batch-Einfügungen (optimiert)
    
    READ-TESTS (Szenario B):
        - Single Reads: find_one() für Einzeldokument-Abruf
        - Batch Reads: find() mit $in für mehrere IDs
        - Filtered Reads: find() mit Metadaten-Filter
    
    Die Tests werden sowohl synchron als auch asynchron durchgeführt.
    """
    
    DATABASE_NAME = "MongoDB"
    
    TEST_DESCRIPTION = """
    MongoDB Document Store Performance Tests
    
    WARUM: MongoDB speichert die Chunk-Dokumente im RAG-System.
           Nach der Vektorsuche werden Chunks per ID geladen.
    
    HYPOTHESE:
        - insert_many() ist 5-10x schneller als insert_one()
        - $in-Query ist effizienter als mehrere find_one()
        - Async zeigt höheren Durchsatz bei parallelen Zugriffen
    
    REFERENZ: Modul 5 & 6 (Chunking & Datenmodellierung), Modul 8
    """
    
    def __init__(self, context: TestContext):
        """Initialisiert den MongoDB-Test."""
        super().__init__(context)
        
        if not HAS_PYMONGO:
            raise ImportError(
                "pymongo nicht installiert. "
                "Installiere mit: pip install pymongo"
            )
        
        # MongoDB-Konfiguration
        mongo_config = self.config.get("databases", {}).get("mongodb", {})
        self.host = mongo_config.get("host", "localhost")
        self.port = mongo_config.get("port", 27017)
        self.database_name = mongo_config.get("database", "rag_performance_test")
        self.collection_name = mongo_config.get("collection", "chunks")
        
        # Clients
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self.async_client = None
        
        # Testdaten
        self.test_chunks: list[dict] = []
        self.inserted_ids: list[ObjectId] = []
    
    def setup(self) -> None:
        """
        Bereitet den MongoDB-Test vor.
        
        - Verbindung herstellen
        - Collection leeren
        - Testdaten generieren
        - Index erstellen (für gefilterte Queries)
        """
        logger.info(f"Verbinde zu MongoDB: {self.host}:{self.port}")
        
        # Synchroner Client
        self.client = MongoClient(
            host=self.host,
            port=self.port,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        
        # Verbindung testen
        self.client.admin.command("ping")
        logger.info("✓ MongoDB-Verbindung hergestellt")
        
        # Datenbank und Collection
        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]
        
        # Collection leeren
        self.collection.drop()
        logger.info("✓ Collection geleert")
        
        # Index auf Metadaten erstellen (für gefilterte Queries)
        self.collection.create_index([("metadata.category", pymongo.ASCENDING)])
        logger.info("✓ Index auf metadata.category erstellt")
        
        # Testdaten generieren
        logger.info(f"Generiere {self.num_operations} Chunk-Dokumente...")
        self.test_chunks = list(
            self.data_generator.generate_chunks(self.num_operations)
        )
        logger.info(f"✓ {len(self.test_chunks)} Testdaten generiert")
    
    def teardown(self) -> None:
        """
        Räumt nach dem Test auf.
        
        - Collection leeren
        - Verbindung schließen
        """
        if self.client:
            try:
                if self.collection:
                    self.collection.drop()
                self.client.close()
                logger.info("✓ MongoDB-Verbindung geschlossen")
            except Exception as e:
                logger.warning(f"Fehler beim Schließen der MongoDB-Verbindung: {e}")
        
        # Testdaten löschen
        self.test_chunks.clear()
        self.inserted_ids.clear()
    
    def warmup(self) -> None:
        """
        Führt Warmup-Operationen durch.
        """
        warmup_docs = [
            {"warmup_id": i, "data": f"warmup_{i}"}
            for i in range(self.warmup_operations)
        ]
        
        # Einfügen
        result = self.collection.insert_many(warmup_docs)
        
        # Lesen
        for doc_id in result.inserted_ids[:10]:
            self.collection.find_one({"_id": doc_id})
        
        # Löschen
        self.collection.delete_many({"warmup_id": {"$exists": True}})
    
    def _run_tests(self) -> None:
        """
        Führt alle MongoDB-Tests aus.
        """
        # =====================================================================
        # SYNCHRONE TESTS
        # =====================================================================
        
        # Write-Tests
        self._test_single_inserts()
        
        # Collection für Bulk-Test leeren
        self.collection.drop()
        self.collection.create_index([("metadata.category", pymongo.ASCENDING)])
        self._test_bulk_inserts()
        
        # Read-Tests (Daten sind jetzt in MongoDB)
        self._test_single_reads()
        self._test_batch_reads()
        self._test_filtered_reads()
        
        # =====================================================================
        # ASYNCHRONE TESTS
        # =====================================================================
        
        if HAS_MOTOR:
            asyncio.run(self._run_async_tests())
        else:
            logger.warning(
                "Asynchrone MongoDB-Tests übersprungen "
                "(motor nicht verfügbar)"
            )
    
    # =========================================================================
    # SYNCHRONE WRITE-TESTS
    # =========================================================================
    
    def _test_single_inserts(self) -> None:
        """
        Test: Single Inserts (einzelne insert_one() Operationen)
        
        KONTEXT:
            Die naive Implementierung: Jedes Dokument wird einzeln
            eingefügt. Jeder insert_one() ist ein Netzwerk-Roundtrip.
            
            Dies ist typisch für Ingest-Prozesse, die Dokumente
            nacheinander verarbeiten.
        
        ERWARTUNG:
            Deutlich langsamer als Bulk-Insert
        """
        logger.info("Test: Single Inserts (insert_one)")
        
        latencies = []
        self.inserted_ids.clear()
        
        # Collection leeren
        self.collection.drop()
        self.collection.create_index([("metadata.category", pymongo.ASCENDING)])
        
        total_start = time.perf_counter_ns()
        
        for chunk in self.test_chunks:
            # Neues Dokument erstellen (ohne _id für automatische Generierung)
            doc = {k: v for k, v in chunk.items() if k != "_id"}
            
            start = time.perf_counter_ns()
            result = self.collection.insert_one(doc)
            end = time.perf_counter_ns()
            
            self.inserted_ids.append(result.inserted_id)
            latencies.append(ns_to_ms(end - start))
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="MongoDB Single insert_one",
            operation_type="write",
            latencies_ms=latencies,
            total_operations=len(self.test_chunks),
            total_duration_ms=total_duration_ms,
            notes="Einzelne insert_one() pro Dokument"
        )
    
    def _test_bulk_inserts(self) -> None:
        """
        Test: Bulk Inserts (insert_many)
        
        KONTEXT:
            insert_many() sendet mehrere Dokumente in einem
            Batch an MongoDB. Der Server verarbeitet sie
            effizienter als einzelne Inserts.
            
            Dies ist die empfohlene Methode für Ingest-Prozesse!
        
        ERWARTUNG:
            5-10x schneller als Single Inserts
        
        REFERENZ:
            Modul 8: Performance-Myth-Busting
        """
        logger.info("Test: Bulk Inserts (insert_many)")
        
        batch_latencies = []
        self.inserted_ids.clear()
        
        total_start = time.perf_counter_ns()
        
        for batch_start in range(0, len(self.test_chunks), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(self.test_chunks))
            batch_docs = [
                {k: v for k, v in chunk.items() if k != "_id"}
                for chunk in self.test_chunks[batch_start:batch_end]
            ]
            
            batch_start_time = time.perf_counter_ns()
            result = self.collection.insert_many(batch_docs)
            batch_end_time = time.perf_counter_ns()
            
            self.inserted_ids.extend(result.inserted_ids)
            
            batch_duration = ns_to_ms(batch_end_time - batch_start_time)
            ops_in_batch = len(batch_docs)
            latency_per_op = batch_duration / ops_in_batch
            
            batch_latencies.extend([latency_per_op] * ops_in_batch)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="MongoDB Bulk insert_many",
            operation_type="write",
            latencies_ms=batch_latencies,
            total_operations=len(self.test_chunks),
            total_duration_ms=total_duration_ms,
            batch_size=self.batch_size,
            notes=f"insert_many() mit Batch-Größe {self.batch_size}"
        )
    
    # =========================================================================
    # SYNCHRONE READ-TESTS
    # =========================================================================
    
    def _test_single_reads(self) -> None:
        """
        Test: Single Reads (find_one)
        
        KONTEXT:
            find_one() ist der typische Abruf eines Chunks nach ID.
            Nach der Vektorsuche werden die gefundenen IDs verwendet,
            um die vollständigen Chunks zu laden.
        
        ERWARTUNG:
            Schnelle Einzelabrufe (unter 5ms P99)
        """
        logger.info("Test: Single Reads (find_one)")
        
        latencies = []
        
        for doc_id in self.inserted_ids:
            start = time.perf_counter_ns()
            self.collection.find_one({"_id": doc_id})
            end = time.perf_counter_ns()
            latencies.append(ns_to_ms(end - start))
        
        total_duration_ms = sum(latencies)
        
        self.record_result(
            test_name="MongoDB Single find_one",
            operation_type="read",
            latencies_ms=latencies,
            total_operations=len(self.inserted_ids),
            total_duration_ms=total_duration_ms,
            notes="Einzelne find_one() pro Dokument"
        )
    
    def _test_batch_reads(self) -> None:
        """
        Test: Batch Reads ($in Query)
        
        KONTEXT:
            Nach einer Vektorsuche mit top_k=10 müssen 10 Chunks
            geladen werden. Statt 10 einzelne find_one() Aufrufe
            kann ein find() mit $in-Operator verwendet werden.
            
            Dies ist effizienter, da nur ein Netzwerk-Roundtrip nötig ist.
        
        ERWARTUNG:
            Deutlich schneller als N einzelne find_one()
        """
        logger.info("Test: Batch Reads ($in Query)")
        
        batch_latencies = []
        
        # Typische RAG-Szenarien: 5-10 Chunks auf einmal laden
        read_batch_size = 10
        
        total_start = time.perf_counter_ns()
        
        for batch_start in range(0, len(self.inserted_ids), read_batch_size):
            batch_end = min(batch_start + read_batch_size, len(self.inserted_ids))
            batch_ids = self.inserted_ids[batch_start:batch_end]
            
            batch_start_time = time.perf_counter_ns()
            
            # $in Query für mehrere IDs
            cursor = self.collection.find({"_id": {"$in": batch_ids}})
            _ = list(cursor)  # Cursor materialisieren
            
            batch_end_time = time.perf_counter_ns()
            
            batch_duration = ns_to_ms(batch_end_time - batch_start_time)
            ops_in_batch = len(batch_ids)
            latency_per_op = batch_duration / ops_in_batch
            
            batch_latencies.extend([latency_per_op] * ops_in_batch)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="MongoDB Batch find ($in)",
            operation_type="read",
            latencies_ms=batch_latencies,
            total_operations=len(self.inserted_ids),
            total_duration_ms=total_duration_ms,
            batch_size=read_batch_size,
            notes=f"find() mit $in, Batch-Größe {read_batch_size}"
        )
    
    def _test_filtered_reads(self) -> None:
        """
        Test: Filtered Reads (Metadaten-Filter)
        
        KONTEXT:
            In manchen Fällen werden Chunks nach Metadaten gefiltert,
            z.B. nur Chunks aus einer bestimmten Kategorie oder Quelle.
            
            Dies ist relevant für Pre-Filtering vor der Vektorsuche
            oder für kategorisierte Suchergebnisse.
        
        ERWARTUNG:
            Mit Index: Schnell (Index-Scan)
            Ohne Index: Langsam (Collection-Scan)
        """
        logger.info("Test: Filtered Reads (mit Index)")
        
        latencies = []
        
        # Alle Kategorien aus den Testdaten extrahieren
        categories = self.data_generator.categories
        
        total_start = time.perf_counter_ns()
        
        # Für jede Kategorie eine Query ausführen
        for category in categories:
            start = time.perf_counter_ns()
            
            cursor = self.collection.find(
                {"metadata.category": category}
            ).limit(100)  # Limit wie in echten Szenarien
            _ = list(cursor)
            
            end = time.perf_counter_ns()
            latencies.append(ns_to_ms(end - start))
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="MongoDB Filtered find",
            operation_type="read",
            latencies_ms=latencies,
            total_operations=len(categories),
            total_duration_ms=total_duration_ms,
            notes="find() mit Metadaten-Filter (indiziert)"
        )
    
    # =========================================================================
    # ASYNCHRONE TESTS
    # =========================================================================
    
    async def _run_async_tests(self) -> None:
        """
        Führt asynchrone MongoDB-Tests aus.
        """
        logger.info("Starte asynchrone MongoDB-Tests...")
        
        # Motor Async-Client erstellen
        self.async_client = motor.motor_asyncio.AsyncIOMotorClient(
            host=self.host,
            port=self.port,
        )
        
        async_db = self.async_client[self.database_name]
        async_collection = async_db[self.collection_name]
        
        try:
            await self.async_client.admin.command("ping")
            
            # Async Write-Test
            await self._test_async_inserts(async_collection)
            
            # Async Read-Test
            await self._test_async_reads(async_collection)
            
        finally:
            self.async_client.close()
    
    async def _test_async_inserts(self, collection) -> None:
        """
        Test: Asynchrone Inserts mit parallelen Clients
        """
        logger.info(f"Test: Async Inserts ({self.concurrent_clients} Clients)")
        
        # Collection leeren
        await collection.drop()
        await collection.create_index([("metadata.category", pymongo.ASCENDING)])
        
        latencies = []
        latency_lock = asyncio.Lock()
        new_ids = []
        ids_lock = asyncio.Lock()
        
        async def insert_batch(docs: list[dict]):
            """Fügt einen Batch von Dokumenten asynchron ein."""
            local_latencies = []
            for doc in docs:
                clean_doc = {k: v for k, v in doc.items() if k != "_id"}
                
                start = time.perf_counter_ns()
                result = await collection.insert_one(clean_doc)
                end = time.perf_counter_ns()
                
                local_latencies.append(ns_to_ms(end - start))
                
                async with ids_lock:
                    new_ids.append(result.inserted_id)
            
            async with latency_lock:
                latencies.extend(local_latencies)
        
        # Chunks auf Clients aufteilen
        chunk_size = len(self.test_chunks) // self.concurrent_clients
        tasks = []
        
        total_start = time.perf_counter_ns()
        
        for i in range(self.concurrent_clients):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < self.concurrent_clients - 1 else len(self.test_chunks)
            
            tasks.append(insert_batch(self.test_chunks[start_idx:end_idx]))
        
        await asyncio.gather(*tasks)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        # IDs für Read-Tests speichern
        self.inserted_ids = new_ids
        
        self.record_result(
            test_name="MongoDB Async insert_one",
            operation_type="write",
            latencies_ms=latencies,
            total_operations=len(self.test_chunks),
            total_duration_ms=total_duration_ms,
            is_async=True,
            concurrent_clients=self.concurrent_clients,
            notes=f"{self.concurrent_clients} parallele Clients"
        )
    
    async def _test_async_reads(self, collection) -> None:
        """
        Test: Asynchrone Reads mit parallelen Clients
        """
        logger.info(f"Test: Async Reads ({self.concurrent_clients} Clients)")
        
        latencies = []
        latency_lock = asyncio.Lock()
        
        async def read_batch(doc_ids: list):
            """Liest einen Batch von Dokumenten asynchron."""
            local_latencies = []
            for doc_id in doc_ids:
                start = time.perf_counter_ns()
                await collection.find_one({"_id": doc_id})
                end = time.perf_counter_ns()
                local_latencies.append(ns_to_ms(end - start))
            
            async with latency_lock:
                latencies.extend(local_latencies)
        
        chunk_size = len(self.inserted_ids) // self.concurrent_clients
        tasks = []
        
        total_start = time.perf_counter_ns()
        
        for i in range(self.concurrent_clients):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < self.concurrent_clients - 1 else len(self.inserted_ids)
            
            tasks.append(read_batch(self.inserted_ids[start_idx:end_idx]))
        
        await asyncio.gather(*tasks)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="MongoDB Async find_one",
            operation_type="read",
            latencies_ms=latencies,
            total_operations=len(self.inserted_ids),
            total_duration_ms=total_duration_ms,
            is_async=True,
            concurrent_clients=self.concurrent_clients,
            notes=f"{self.concurrent_clients} parallele Clients"
        )
