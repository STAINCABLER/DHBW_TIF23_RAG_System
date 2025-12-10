"""
Redis Performance Tests
========================

Performance-Tests für Redis als Key-Value Store im RAG-System.

WARUM TESTEN WIR DAS?
---------------------
Redis wird im RAG-System für folgende Szenarien eingesetzt (Modul 4 & 8):
    - Session-Management: Speicherung von User-Sessions
    - Rate-Limiting: Zähler für API-Aufrufe pro Zeitfenster
    - Caching: Zwischenspeicherung häufig abgerufener Chunks
    - Queue: Asynchrone Verarbeitung von Ingest-Jobs

ERWARTUNGSHALTUNG (HYPOTHESE):
------------------------------
1. Pipeline-Operationen sind 10-20x schneller als Einzeloperationen
   (Grund: Reduzierung des Roundtrip-Overheads)
   
2. P99 Latenz für einzelne GET/SET sollte unter 2ms liegen
   (Grund: Redis ist In-Memory, kritischer Pfad)
   
3. Asynchrone Tests zeigen höheren Durchsatz bei ähnlicher Latenz
   (Grund: Bessere Nutzung von I/O-Wartezeiten)

REFERENZ:
---------
- Modul 4: Query Paths bestimmen die Systemkosten
- Modul 8: Performance-Myth-Busting (Redis naiv vs. Pipeline)

Autor: RAG Performance Test Suite
"""

import time
import asyncio
import logging
from typing import Optional

# Redis-Treiber
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    import redis.asyncio as aioredis
    HAS_AIOREDIS = True
except ImportError:
    HAS_AIOREDIS = False

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import ns_to_ms

logger = logging.getLogger(__name__)


class RedisPerformanceTest(BasePerformanceTest):
    """
    Redis Performance Tests - Synchron und Asynchron.
    
    Dieser Test deckt folgende Szenarien ab:
    
    WRITE-TESTS (Szenario A):
        - Naive Writes: Einzelne SET-Operationen (Baseline)
        - Pipeline Writes: Batch-SET mit Redis Pipeline (optimiert)
    
    READ-TESTS (Szenario B):
        - Naive Reads: Einzelne GET-Operationen
        - Pipeline Reads: Batch-GET mit Redis Pipeline
        - MGET: Multi-Key GET in einem Aufruf
    
    Die Tests werden sowohl synchron als auch asynchron durchgeführt,
    um den Einfluss von Concurrency zu messen.
    """
    
    DATABASE_NAME = "Redis"
    
    TEST_DESCRIPTION = """
    Redis Key-Value Store Performance Tests
    
    WARUM: Redis ist der primäre Cache und Session-Store im RAG-System.
           Er liegt im kritischen Pfad für Rate-Limiting und Session-Checks.
    
    HYPOTHESE:
        - Pipeline/Batch-Operationen sind 10-20x schneller
        - P99 Latenz unter 2ms für Einzeloperationen
        - Asynchrone Tests zeigen höheren Durchsatz
    
    REFERENZ: Modul 4 (Query Paths), Modul 8 (Performance-Myth-Busting)
    """
    
    def __init__(self, context: TestContext):
        """Initialisiert den Redis-Test."""
        super().__init__(context)
        
        if not HAS_REDIS:
            raise ImportError(
                "redis-py nicht installiert. "
                "Installiere mit: pip install redis"
            )
        
        # Redis-Konfiguration
        redis_config = self.config.get("databases", {}).get("redis", {})
        self.host = redis_config.get("host", "localhost")
        self.port = redis_config.get("port", 6379)
        self.password = redis_config.get("password")
        self.db = redis_config.get("db", 0)
        
        # Clients (werden in setup() initialisiert)
        self.client: Optional[redis.Redis] = None
        self.async_client = None
        
        # Testdaten
        self.test_keys: list[str] = []
        self.test_values: list[str] = []
    
    def setup(self) -> None:
        """
        Bereitet den Redis-Test vor.
        
        - Verbindung herstellen
        - Datenbank leeren (FLUSHDB)
        - Testdaten generieren
        """
        logger.info(f"Verbinde zu Redis: {self.host}:{self.port}")
        
        # Synchroner Client
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            decode_responses=True,  # Strings statt Bytes
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        
        # Verbindung testen
        self.client.ping()
        logger.info("✓ Redis-Verbindung hergestellt")
        
        # Datenbank leeren
        self.client.flushdb()
        logger.info("✓ Redis-Datenbank geleert")
        
        # Testdaten generieren
        logger.info(f"Generiere {self.num_operations} Key-Value Paare...")
        for key, value in self.data_generator.generate_key_value_pairs(
            self.num_operations
        ):
            self.test_keys.append(key)
            self.test_values.append(value)
        
        logger.info(f"✓ {len(self.test_keys)} Testdaten generiert")
    
    def teardown(self) -> None:
        """
        Räumt nach dem Test auf.
        
        - Datenbank leeren
        - Verbindung schließen
        """
        if self.client:
            try:
                self.client.flushdb()
                self.client.close()
                logger.info("✓ Redis-Verbindung geschlossen")
            except Exception as e:
                logger.warning(f"Fehler beim Schließen der Redis-Verbindung: {e}")
        
        # Testdaten löschen
        self.test_keys.clear()
        self.test_values.clear()
    
    def warmup(self) -> None:
        """
        Führt Warmup-Operationen durch.
        
        Schreibt und liest einige Werte, um den Connection-Pool
        zu initialisieren und JIT-Effekte zu minimieren.
        """
        for i in range(self.warmup_operations):
            key = f"warmup:{i}"
            self.client.set(key, f"warmup_value_{i}")
            self.client.get(key)
            self.client.delete(key)
    
    def _run_tests(self) -> None:
        """
        Führt alle Redis-Tests aus.
        
        Reihenfolge:
        1. Synchrone Write-Tests
        2. Synchrone Read-Tests
        3. Asynchrone Tests (falls verfügbar)
        """
        # =====================================================================
        # SYNCHRONE TESTS
        # =====================================================================
        
        # Write-Tests
        self._test_naive_writes()
        self._test_pipeline_writes()
        
        # Read-Tests (Daten sind jetzt in Redis)
        self._test_naive_reads()
        self._test_pipeline_reads()
        self._test_mget()
        
        # =====================================================================
        # ASYNCHRONE TESTS
        # =====================================================================
        
        if HAS_AIOREDIS:
            asyncio.run(self._run_async_tests())
        else:
            logger.warning(
                "Asynchrone Redis-Tests übersprungen "
                "(redis.asyncio nicht verfügbar)"
            )
    
    # =========================================================================
    # SYNCHRONE WRITE-TESTS
    # =========================================================================
    
    def _test_naive_writes(self) -> None:
        """
        Test: Naive Writes (einzelne SET-Operationen)
        
        KONTEXT:
            Dies ist die "naive" Implementierung, die oft von Anfängern
            verwendet wird. Jeder SET-Befehl wartet auf die Antwort des
            Servers, bevor der nächste gesendet wird.
            
            Das Problem: Jede Operation hat einen Roundtrip zum Server.
            Bei 10.000 Operationen sind das 10.000 Roundtrips!
        
        ERWARTUNG:
            Deutlich langsamer als Pipeline (10-20x)
        """
        logger.info("Test: Naive Writes (einzelne SET)")
        
        latencies = []
        
        # Datenbank vorher leeren
        self.client.flushdb()
        
        # Gesamtzeit messen
        total_start = time.perf_counter_ns()
        
        for i, (key, value) in enumerate(zip(self.test_keys, self.test_values)):
            start = time.perf_counter_ns()
            self.client.set(key, value)
            end = time.perf_counter_ns()
            latencies.append(ns_to_ms(end - start))
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="Redis Naive SET",
            operation_type="write",
            latencies_ms=latencies,
            total_operations=len(self.test_keys),
            total_duration_ms=total_duration_ms,
            notes="Einzelne SET-Operationen mit Roundtrip pro Operation"
        )
    
    def _test_pipeline_writes(self) -> None:
        """
        Test: Pipeline Writes (Batch-SET)
        
        KONTEXT:
            Redis-Pipelines erlauben das Senden mehrerer Befehle,
            ohne auf die Antwort jedes einzelnen zu warten.
            
            Alle Befehle werden gesammelt und in einem Netzwerk-Paket
            gesendet. Die Antworten kommen dann alle zusammen zurück.
            
            Dies reduziert den Roundtrip-Overhead drastisch!
        
        ERWARTUNG:
            10-20x schneller als naive Writes
        
        REFERENZ:
            Modul 8: Performance-Myth-Busting
        """
        logger.info("Test: Pipeline Writes (Batch-SET)")
        
        # Datenbank vorher leeren
        self.client.flushdb()
        
        # Wir messen die Zeit pro Batch
        batch_latencies = []
        
        total_start = time.perf_counter_ns()
        
        # In Batches aufteilen
        for batch_start in range(0, len(self.test_keys), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(self.test_keys))
            
            batch_start_time = time.perf_counter_ns()
            
            # Pipeline erstellen und befüllen
            pipe = self.client.pipeline(transaction=False)
            for i in range(batch_start, batch_end):
                pipe.set(self.test_keys[i], self.test_values[i])
            
            # Pipeline ausführen
            pipe.execute()
            
            batch_end_time = time.perf_counter_ns()
            
            # Latenz pro Operation im Batch berechnen
            batch_duration = ns_to_ms(batch_end_time - batch_start_time)
            ops_in_batch = batch_end - batch_start
            latency_per_op = batch_duration / ops_in_batch
            
            # Für jede Operation im Batch die durchschnittliche Latenz speichern
            batch_latencies.extend([latency_per_op] * ops_in_batch)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="Redis Pipeline SET",
            operation_type="write",
            latencies_ms=batch_latencies,
            total_operations=len(self.test_keys),
            total_duration_ms=total_duration_ms,
            batch_size=self.batch_size,
            notes=f"Pipeline mit Batch-Größe {self.batch_size}"
        )
    
    # =========================================================================
    # SYNCHRONE READ-TESTS
    # =========================================================================
    
    def _test_naive_reads(self) -> None:
        """
        Test: Naive Reads (einzelne GET-Operationen)
        
        KONTEXT:
            Wie bei Writes: Jede GET-Operation wartet auf die Antwort.
            Dies ist typisch für einfache Cache-Lookups.
        
        ERWARTUNG:
            Ähnlich langsam wie naive Writes
        """
        logger.info("Test: Naive Reads (einzelne GET)")
        
        latencies = []
        
        for key in self.test_keys:
            start = time.perf_counter_ns()
            self.client.get(key)
            end = time.perf_counter_ns()
            latencies.append(ns_to_ms(end - start))
        
        total_duration_ms = sum(latencies)
        
        self.record_result(
            test_name="Redis Naive GET",
            operation_type="read",
            latencies_ms=latencies,
            total_operations=len(self.test_keys),
            total_duration_ms=total_duration_ms,
            notes="Einzelne GET-Operationen"
        )
    
    def _test_pipeline_reads(self) -> None:
        """
        Test: Pipeline Reads (Batch-GET)
        
        KONTEXT:
            Analog zu Pipeline Writes werden mehrere GET-Befehle
            in einer Pipeline gesammelt und zusammen ausgeführt.
        
        ERWARTUNG:
            10-20x schneller als naive Reads
        """
        logger.info("Test: Pipeline Reads (Batch-GET)")
        
        batch_latencies = []
        
        total_start = time.perf_counter_ns()
        
        for batch_start in range(0, len(self.test_keys), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(self.test_keys))
            
            batch_start_time = time.perf_counter_ns()
            
            pipe = self.client.pipeline(transaction=False)
            for i in range(batch_start, batch_end):
                pipe.get(self.test_keys[i])
            
            pipe.execute()
            
            batch_end_time = time.perf_counter_ns()
            
            batch_duration = ns_to_ms(batch_end_time - batch_start_time)
            ops_in_batch = batch_end - batch_start
            latency_per_op = batch_duration / ops_in_batch
            
            batch_latencies.extend([latency_per_op] * ops_in_batch)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="Redis Pipeline GET",
            operation_type="read",
            latencies_ms=batch_latencies,
            total_operations=len(self.test_keys),
            total_duration_ms=total_duration_ms,
            batch_size=self.batch_size,
            notes=f"Pipeline mit Batch-Größe {self.batch_size}"
        )
    
    def _test_mget(self) -> None:
        """
        Test: MGET (Multi-Key GET in einem Befehl)
        
        KONTEXT:
            MGET ist ein spezieller Redis-Befehl, der mehrere Keys
            in einer einzigen Operation abruft. Dies ist noch effizienter
            als eine Pipeline, da es ein einziger Befehl ist.
            
            Typischer Anwendungsfall: Abruf mehrerer Chunk-IDs nach
            einer Vektorsuche.
        
        ERWARTUNG:
            Ähnlich schnell wie Pipeline, möglicherweise etwas besser
        """
        logger.info("Test: MGET (Multi-Key GET)")
        
        batch_latencies = []
        
        total_start = time.perf_counter_ns()
        
        for batch_start in range(0, len(self.test_keys), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(self.test_keys))
            batch_keys = self.test_keys[batch_start:batch_end]
            
            batch_start_time = time.perf_counter_ns()
            
            self.client.mget(batch_keys)
            
            batch_end_time = time.perf_counter_ns()
            
            batch_duration = ns_to_ms(batch_end_time - batch_start_time)
            ops_in_batch = len(batch_keys)
            latency_per_op = batch_duration / ops_in_batch
            
            batch_latencies.extend([latency_per_op] * ops_in_batch)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="Redis MGET",
            operation_type="read",
            latencies_ms=batch_latencies,
            total_operations=len(self.test_keys),
            total_duration_ms=total_duration_ms,
            batch_size=self.batch_size,
            notes="Multi-Key GET in einem Befehl"
        )
    
    # =========================================================================
    # ASYNCHRONE TESTS
    # =========================================================================
    
    async def _run_async_tests(self) -> None:
        """
        Führt asynchrone Redis-Tests aus.
        
        Diese Tests simulieren mehrere parallele Clients, die
        gleichzeitig auf Redis zugreifen.
        """
        logger.info("Starte asynchrone Redis-Tests...")
        
        # Async-Client erstellen
        self.async_client = aioredis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            decode_responses=True,
        )
        
        try:
            await self.async_client.ping()
            
            # Async Write-Test
            await self._test_async_writes()
            
            # Async Read-Test
            await self._test_async_reads()
            
        finally:
            await self.async_client.close()
    
    async def _test_async_writes(self) -> None:
        """
        Test: Asynchrone Writes mit parallelen Clients
        
        KONTEXT:
            In einer echten Anwendung greifen mehrere Requests
            gleichzeitig auf Redis zu. Dieser Test simuliert
            N parallele Clients, die SETs ausführen.
        
        ERWARTUNG:
            Höherer Gesamtdurchsatz als synchron,
            aber möglicherweise höhere P99-Latenz
        """
        logger.info(f"Test: Async Writes ({self.concurrent_clients} Clients)")
        
        # Datenbank leeren
        await self.async_client.flushdb()
        
        latencies = []
        latency_lock = asyncio.Lock()
        
        async def write_batch(keys: list, values: list):
            """Schreibt einen Batch von Key-Value Paaren."""
            local_latencies = []
            for key, value in zip(keys, values):
                start = time.perf_counter_ns()
                await self.async_client.set(key, value)
                end = time.perf_counter_ns()
                local_latencies.append(ns_to_ms(end - start))
            
            async with latency_lock:
                latencies.extend(local_latencies)
        
        # Keys und Values auf Clients aufteilen
        chunk_size = len(self.test_keys) // self.concurrent_clients
        tasks = []
        
        total_start = time.perf_counter_ns()
        
        for i in range(self.concurrent_clients):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < self.concurrent_clients - 1 else len(self.test_keys)
            
            tasks.append(
                write_batch(
                    self.test_keys[start_idx:end_idx],
                    self.test_values[start_idx:end_idx]
                )
            )
        
        await asyncio.gather(*tasks)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="Redis Async SET",
            operation_type="write",
            latencies_ms=latencies,
            total_operations=len(self.test_keys),
            total_duration_ms=total_duration_ms,
            is_async=True,
            concurrent_clients=self.concurrent_clients,
            notes=f"{self.concurrent_clients} parallele Clients"
        )
    
    async def _test_async_reads(self) -> None:
        """
        Test: Asynchrone Reads mit parallelen Clients
        
        KONTEXT:
            Simuliert parallele Lese-Anfragen, wie sie bei
            mehreren gleichzeitigen API-Requests auftreten.
        """
        logger.info(f"Test: Async Reads ({self.concurrent_clients} Clients)")
        
        latencies = []
        latency_lock = asyncio.Lock()
        
        async def read_batch(keys: list):
            """Liest einen Batch von Keys."""
            local_latencies = []
            for key in keys:
                start = time.perf_counter_ns()
                await self.async_client.get(key)
                end = time.perf_counter_ns()
                local_latencies.append(ns_to_ms(end - start))
            
            async with latency_lock:
                latencies.extend(local_latencies)
        
        chunk_size = len(self.test_keys) // self.concurrent_clients
        tasks = []
        
        total_start = time.perf_counter_ns()
        
        for i in range(self.concurrent_clients):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < self.concurrent_clients - 1 else len(self.test_keys)
            
            tasks.append(read_batch(self.test_keys[start_idx:end_idx]))
        
        await asyncio.gather(*tasks)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="Redis Async GET",
            operation_type="read",
            latencies_ms=latencies,
            total_operations=len(self.test_keys),
            total_duration_ms=total_duration_ms,
            is_async=True,
            concurrent_clients=self.concurrent_clients,
            notes=f"{self.concurrent_clients} parallele Clients"
        )
