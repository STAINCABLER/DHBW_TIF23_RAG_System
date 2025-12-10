"""
PostgreSQL Performance Tests
=============================

Performance-Tests für PostgreSQL als relationale Datenbank im RAG-System.

WARUM TESTEN WIR DAS?
---------------------
PostgreSQL wird im RAG-System für ACID-kritische Daten eingesetzt (Modul 4 & 5):
    - User-Profile: Strukturierte Benutzerdaten
    - Berechtigungen: Zugriffskontrolle (RBAC)
    - Audit-Logs: Compliance-relevante Protokolle
    - Metadaten: Strukturierte Metadaten zu Dokumenten

ERWARTUNGSHALTUNG (HYPOTHESE):
------------------------------
1. Transaktionsbatch ist 50-100x schneller als einzelne Commits
   (Grund: WAL-Schreibvorgänge und fsync werden gebündelt)
   
2. Indizierte Queries sind 10-100x schneller als ohne Index
   (Grund: B-Tree Index vs. Sequential Scan)
   
3. P99 Latenz für SELECT mit Index sollte unter 5ms liegen

REFERENZ:
---------
- Modul 4: Query Paths bestimmen die Systemkosten
- Modul 8: Performance-Myth-Busting (PostgreSQL Commits)

Autor: RAG Performance Test Suite
"""

import time
import asyncio
import logging
from typing import Optional

# PostgreSQL-Treiber
try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import execute_batch, execute_values
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import ns_to_ms

logger = logging.getLogger(__name__)


class PostgresPerformanceTest(BasePerformanceTest):
    """
    PostgreSQL Performance Tests - Synchron und Asynchron.
    
    Dieser Test deckt folgende Szenarien ab:
    
    WRITE-TESTS (Szenario A):
        - Single Commits: Jedes INSERT mit eigenem COMMIT (Baseline)
        - Transactional Batch: Alle INSERTs in einer Transaktion (optimiert)
        - execute_batch: psycopg2 optimierte Batch-Ausführung
    
    READ-TESTS (Szenario B):
        - Simple SELECT: Abruf per Primary Key
        - Filtered SELECT: Query mit WHERE-Clause
        - JOIN Query: Verknüpfung mehrerer Tabellen
    
    INDEX-TESTS:
        - Mit Index: SELECT auf indizierter Spalte
        - Ohne Index: SELECT auf nicht-indizierter Spalte
    """
    
    DATABASE_NAME = "PostgreSQL"
    
    TEST_DESCRIPTION = """
    PostgreSQL Relationale Datenbank Performance Tests
    
    WARUM: PostgreSQL speichert strukturierte, ACID-kritische Daten
           (User-Profile, Berechtigungen, Audit-Logs).
    
    HYPOTHESE:
        - Transaktionsbatch ist 50-100x schneller als Single Commits
        - Indizierte Queries sind 10-100x schneller
        - P99 Latenz unter 5ms für indizierte SELECTs
    
    REFERENZ: Modul 4 (Query Paths), Modul 8 (PostgreSQL Commits)
    """
    
    def __init__(self, context: TestContext):
        """Initialisiert den PostgreSQL-Test."""
        super().__init__(context)
        
        if not HAS_PSYCOPG2:
            raise ImportError(
                "psycopg2 nicht installiert. "
                "Installiere mit: pip install psycopg2-binary"
            )
        
        # PostgreSQL-Konfiguration
        pg_config = self.config.get("databases", {}).get("postgres", {})
        self.host = pg_config.get("host", "localhost")
        self.port = pg_config.get("port", 5432)
        self.database = pg_config.get("database", "rag_performance_test")
        self.user = pg_config.get("user", "postgres")
        self.password = pg_config.get("password", "postgres")
        
        # Clients
        self.conn = None
        self.async_pool = None
        
        # Testdaten
        self.test_users: list[dict] = []
        self.inserted_ids: list[str] = []
    
    def setup(self) -> None:
        """
        Bereitet den PostgreSQL-Test vor.
        
        - Verbindung herstellen
        - Tabellen erstellen
        - Indizes anlegen
        - Testdaten generieren
        """
        logger.info(f"Verbinde zu PostgreSQL: {self.host}:{self.port}")
        
        # Verbindung herstellen
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            connect_timeout=5,
        )
        self.conn.autocommit = False
        
        logger.info("✓ PostgreSQL-Verbindung hergestellt")
        
        # Tabellen erstellen
        self._create_tables()
        
        # Testdaten generieren
        logger.info(f"Generiere {self.num_operations} User-Datensätze...")
        self.test_users = list(
            self.data_generator.generate_users(self.num_operations)
        )
        logger.info(f"✓ {len(self.test_users)} Testdaten generiert")
    
    def _create_tables(self) -> None:
        """Erstellt die Test-Tabellen."""
        with self.conn.cursor() as cur:
            # Alte Tabellen löschen
            cur.execute("DROP TABLE IF EXISTS test_users CASCADE")
            cur.execute("DROP TABLE IF EXISTS test_logs CASCADE")
            
            # Users-Tabelle
            cur.execute("""
                CREATE TABLE test_users (
                    user_id VARCHAR(36) PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    role VARCHAR(50) DEFAULT 'user',
                    -- Spalte ohne Index für Vergleichstests
                    unindexed_field VARCHAR(100)
                )
            """)
            
            # Index auf email
            cur.execute("""
                CREATE INDEX idx_users_email ON test_users(email)
            """)
            
            # Index auf role
            cur.execute("""
                CREATE INDEX idx_users_role ON test_users(role)
            """)
            
            # Logs-Tabelle (für JOIN-Tests)
            cur.execute("""
                CREATE TABLE test_logs (
                    log_id SERIAL PRIMARY KEY,
                    user_id VARCHAR(36) REFERENCES test_users(user_id),
                    action VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.conn.commit()
        
        logger.info("✓ Tabellen erstellt")
    
    def teardown(self) -> None:
        """
        Räumt nach dem Test auf.
        """
        if self.conn:
            try:
                with self.conn.cursor() as cur:
                    cur.execute("DROP TABLE IF EXISTS test_logs CASCADE")
                    cur.execute("DROP TABLE IF EXISTS test_users CASCADE")
                self.conn.commit()
                self.conn.close()
                logger.info("✓ PostgreSQL-Verbindung geschlossen")
            except Exception as e:
                logger.warning(f"Fehler beim Aufräumen: {e}")
        
        self.test_users.clear()
        self.inserted_ids.clear()
    
    def warmup(self) -> None:
        """Führt Warmup-Operationen durch."""
        with self.conn.cursor() as cur:
            for i in range(min(self.warmup_operations, 100)):
                cur.execute(
                    "SELECT 1 WHERE %s = %s",
                    (i, i)
                )
            self.conn.commit()
    
    def _run_tests(self) -> None:
        """Führt alle PostgreSQL-Tests aus."""
        # =====================================================================
        # SYNCHRONE TESTS
        # =====================================================================
        
        # Write-Tests
        self._test_single_commits()
        self._clear_table()
        self._test_transactional_batch()
        self._clear_table()
        self._test_execute_batch()
        
        # Read-Tests (Daten sind jetzt in PostgreSQL)
        self._test_pk_select()
        self._test_indexed_select()
        self._test_unindexed_select()
        
        # =====================================================================
        # ASYNCHRONE TESTS
        # =====================================================================
        
        if HAS_ASYNCPG:
            asyncio.run(self._run_async_tests())
        else:
            logger.warning(
                "Asynchrone PostgreSQL-Tests übersprungen "
                "(asyncpg nicht verfügbar)"
            )
    
    def _clear_table(self) -> None:
        """Leert die test_users Tabelle."""
        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE test_users CASCADE")
            self.conn.commit()
        self.inserted_ids.clear()
    
    # =========================================================================
    # SYNCHRONE WRITE-TESTS
    # =========================================================================
    
    def _test_single_commits(self) -> None:
        """
        Test: Single Commits (jedes INSERT mit eigenem COMMIT)
        
        KONTEXT:
            Dies ist die ineffizienteste Art zu schreiben!
            Jeder COMMIT erzwingt:
            - WAL (Write-Ahead Log) Flush
            - fsync() auf die Festplatte
            - Lock-Release
            
            Bei 10.000 INSERTs sind das 10.000 fsync-Aufrufe!
        
        ERWARTUNG:
            Extrem langsam (50-100x langsamer als Transaktionsbatch)
        
        REFERENZ:
            Modul 8: Performance-Myth-Busting
        """
        logger.info("Test: Single Commits (jedes INSERT mit COMMIT)")
        
        latencies = []
        self.inserted_ids.clear()
        
        self.conn.autocommit = True  # Jeder Befehl ist eigene Transaktion
        
        total_start = time.perf_counter_ns()
        
        with self.conn.cursor() as cur:
            for user in self.test_users:
                start = time.perf_counter_ns()
                
                cur.execute(
                    """
                    INSERT INTO test_users 
                    (user_id, username, email, full_name, is_active, role, unindexed_field)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user["user_id"],
                        user["username"],
                        user["email"],
                        user["full_name"],
                        user["is_active"],
                        user["role"],
                        f"unindexed_{user['user_id'][:8]}"
                    )
                )
                
                end = time.perf_counter_ns()
                
                self.inserted_ids.append(user["user_id"])
                latencies.append(ns_to_ms(end - start))
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.conn.autocommit = False
        
        self.record_result(
            test_name="PostgreSQL Single Commits",
            operation_type="write",
            latencies_ms=latencies,
            total_operations=len(self.test_users),
            total_duration_ms=total_duration_ms,
            notes="Jedes INSERT mit eigenem COMMIT (ineffizient!)"
        )
    
    def _test_transactional_batch(self) -> None:
        """
        Test: Transactional Batch (alle INSERTs in einer Transaktion)
        
        KONTEXT:
            Alle INSERTs werden in einer einzigen Transaktion
            zusammengefasst. Der COMMIT erfolgt erst am Ende.
            
            Dies reduziert die WAL-Schreibvorgänge und fsync-Aufrufe
            drastisch!
        
        ERWARTUNG:
            50-100x schneller als Single Commits
        """
        logger.info("Test: Transactional Batch (eine Transaktion)")
        
        self.inserted_ids.clear()
        latencies = []
        
        total_start = time.perf_counter_ns()
        
        with self.conn.cursor() as cur:
            for user in self.test_users:
                start = time.perf_counter_ns()
                
                cur.execute(
                    """
                    INSERT INTO test_users 
                    (user_id, username, email, full_name, is_active, role, unindexed_field)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user["user_id"],
                        user["username"],
                        user["email"],
                        user["full_name"],
                        user["is_active"],
                        user["role"],
                        f"unindexed_{user['user_id'][:8]}"
                    )
                )
                
                end = time.perf_counter_ns()
                
                self.inserted_ids.append(user["user_id"])
                latencies.append(ns_to_ms(end - start))
        
        # Ein COMMIT am Ende
        commit_start = time.perf_counter_ns()
        self.conn.commit()
        commit_end = time.perf_counter_ns()
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="PostgreSQL Transactional Batch",
            operation_type="write",
            latencies_ms=latencies,
            total_operations=len(self.test_users),
            total_duration_ms=total_duration_ms,
            notes=f"Alle INSERTs in einer Transaktion, COMMIT: {ns_to_ms(commit_end - commit_start):.2f}ms"
        )
    
    def _test_execute_batch(self) -> None:
        """
        Test: execute_batch (psycopg2 optimiert)
        
        KONTEXT:
            psycopg2 bietet execute_batch() als optimierte
            Alternative zu wiederholten execute()-Aufrufen.
            
            Es gruppiert mehrere INSERTs in weniger Netzwerk-Pakete.
        
        ERWARTUNG:
            Schneller als einzelne execute(), ähnlich wie Transaktionsbatch
        """
        logger.info("Test: execute_batch (psycopg2 optimiert)")
        
        self.inserted_ids.clear()
        
        # Daten vorbereiten
        data = [
            (
                user["user_id"],
                user["username"],
                user["email"],
                user["full_name"],
                user["is_active"],
                user["role"],
                f"unindexed_{user['user_id'][:8]}"
            )
            for user in self.test_users
        ]
        
        total_start = time.perf_counter_ns()
        
        with self.conn.cursor() as cur:
            execute_batch(
                cur,
                """
                INSERT INTO test_users 
                (user_id, username, email, full_name, is_active, role, unindexed_field)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                data,
                page_size=self.batch_size
            )
        
        self.conn.commit()
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        # IDs speichern
        self.inserted_ids = [user["user_id"] for user in self.test_users]
        
        # Durchschnittliche Latenz berechnen
        avg_latency = total_duration_ms / len(self.test_users)
        latencies = [avg_latency] * len(self.test_users)
        
        self.record_result(
            test_name="PostgreSQL execute_batch",
            operation_type="write",
            latencies_ms=latencies,
            total_operations=len(self.test_users),
            total_duration_ms=total_duration_ms,
            batch_size=self.batch_size,
            notes=f"psycopg2 execute_batch mit page_size={self.batch_size}"
        )
    
    # =========================================================================
    # SYNCHRONE READ-TESTS
    # =========================================================================
    
    def _test_pk_select(self) -> None:
        """
        Test: Primary Key SELECT
        
        KONTEXT:
            Abruf eines Datensatzes per Primary Key ist der
            schnellste Weg in PostgreSQL (B-Tree Index Lookup).
        
        ERWARTUNG:
            Sehr schnell (unter 1ms P99)
        """
        logger.info("Test: Primary Key SELECT")
        
        latencies = []
        
        with self.conn.cursor() as cur:
            for user_id in self.inserted_ids:
                start = time.perf_counter_ns()
                
                cur.execute(
                    "SELECT * FROM test_users WHERE user_id = %s",
                    (user_id,)
                )
                cur.fetchone()
                
                end = time.perf_counter_ns()
                latencies.append(ns_to_ms(end - start))
        
        total_duration_ms = sum(latencies)
        
        self.record_result(
            test_name="PostgreSQL PK SELECT",
            operation_type="read",
            latencies_ms=latencies,
            total_operations=len(self.inserted_ids),
            total_duration_ms=total_duration_ms,
            notes="SELECT per Primary Key (B-Tree Index)"
        )
    
    def _test_indexed_select(self) -> None:
        """
        Test: Indexed SELECT (auf role-Spalte)
        
        KONTEXT:
            SELECT mit WHERE auf einer indizierten Spalte.
            PostgreSQL nutzt den B-Tree Index für schnellen Zugriff.
        """
        logger.info("Test: Indexed SELECT (role)")
        
        latencies = []
        roles = ["user", "admin", "moderator"]
        
        total_start = time.perf_counter_ns()
        
        with self.conn.cursor() as cur:
            for _ in range(100):  # 100 Queries
                for role in roles:
                    start = time.perf_counter_ns()
                    
                    cur.execute(
                        "SELECT * FROM test_users WHERE role = %s LIMIT 10",
                        (role,)
                    )
                    cur.fetchall()
                    
                    end = time.perf_counter_ns()
                    latencies.append(ns_to_ms(end - start))
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="PostgreSQL Indexed SELECT",
            operation_type="read",
            latencies_ms=latencies,
            total_operations=len(latencies),
            total_duration_ms=total_duration_ms,
            notes="SELECT mit Index auf 'role' Spalte"
        )
    
    def _test_unindexed_select(self) -> None:
        """
        Test: Unindexed SELECT (Sequential Scan)
        
        KONTEXT:
            SELECT auf einer nicht-indizierten Spalte erzwingt
            einen Sequential Scan (alle Zeilen durchsuchen).
            
            Dies zeigt, warum Indizes wichtig sind!
        
        ERWARTUNG:
            Deutlich langsamer als indizierte Selects
        """
        logger.info("Test: Unindexed SELECT (Sequential Scan)")
        
        latencies = []
        
        # Einige unindexed_field Werte zum Suchen
        search_values = [
            f"unindexed_{user_id[:8]}"
            for user_id in self.inserted_ids[:100]
        ]
        
        total_start = time.perf_counter_ns()
        
        with self.conn.cursor() as cur:
            for value in search_values:
                start = time.perf_counter_ns()
                
                cur.execute(
                    "SELECT * FROM test_users WHERE unindexed_field = %s",
                    (value,)
                )
                cur.fetchall()
                
                end = time.perf_counter_ns()
                latencies.append(ns_to_ms(end - start))
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="PostgreSQL Unindexed SELECT",
            operation_type="read",
            latencies_ms=latencies,
            total_operations=len(latencies),
            total_duration_ms=total_duration_ms,
            notes="SELECT ohne Index (Sequential Scan!)"
        )
    
    # =========================================================================
    # ASYNCHRONE TESTS
    # =========================================================================
    
    async def _run_async_tests(self) -> None:
        """Führt asynchrone PostgreSQL-Tests aus."""
        logger.info("Starte asynchrone PostgreSQL-Tests...")
        
        try:
            # Connection Pool erstellen mit Timeout
            self.async_pool = await asyncio.wait_for(
                asyncpg.create_pool(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    min_size=2,
                    max_size=self.concurrent_clients,
                    command_timeout=30,
                ),
                timeout=30.0  # 30 Sekunden Timeout für Pool-Erstellung
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Timeout beim Erstellen des asyncpg Connection Pools. "
                "Asynchrone PostgreSQL-Tests werden übersprungen."
            )
            return
        except Exception as e:
            logger.warning(f"Fehler bei asyncpg: {e}. Async-Tests übersprungen.")
            return
        
        try:
            # Tabelle leeren und neu befüllen
            async with self.async_pool.acquire() as conn:
                await conn.execute("TRUNCATE test_users CASCADE")
            
            # Async Write-Test
            await self._test_async_inserts()
            
            # Async Read-Test
            await self._test_async_selects()
            
        finally:
            await self.async_pool.close()
    
    async def _test_async_inserts(self) -> None:
        """Test: Asynchrone Inserts mit parallelen Clients"""
        logger.info(f"Test: Async Inserts ({self.concurrent_clients} Clients)")
        
        latencies = []
        latency_lock = asyncio.Lock()
        new_ids = []
        ids_lock = asyncio.Lock()
        
        async def insert_batch(users: list[dict]):
            """Fügt einen Batch von Usern asynchron ein."""
            local_latencies = []
            
            async with self.async_pool.acquire() as conn:
                for user in users:
                    start = time.perf_counter_ns()
                    
                    await conn.execute(
                        """
                        INSERT INTO test_users 
                        (user_id, username, email, full_name, is_active, role, unindexed_field)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        user["user_id"],
                        user["username"],
                        user["email"],
                        user["full_name"],
                        user["is_active"],
                        user["role"],
                        f"unindexed_{user['user_id'][:8]}"
                    )
                    
                    end = time.perf_counter_ns()
                    local_latencies.append(ns_to_ms(end - start))
                    
                    async with ids_lock:
                        new_ids.append(user["user_id"])
            
            async with latency_lock:
                latencies.extend(local_latencies)
        
        # Users auf Clients aufteilen
        chunk_size = len(self.test_users) // self.concurrent_clients
        tasks = []
        
        total_start = time.perf_counter_ns()
        
        for i in range(self.concurrent_clients):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < self.concurrent_clients - 1 else len(self.test_users)
            
            tasks.append(insert_batch(self.test_users[start_idx:end_idx]))
        
        await asyncio.gather(*tasks)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.inserted_ids = new_ids
        
        self.record_result(
            test_name="PostgreSQL Async INSERT",
            operation_type="write",
            latencies_ms=latencies,
            total_operations=len(self.test_users),
            total_duration_ms=total_duration_ms,
            is_async=True,
            concurrent_clients=self.concurrent_clients,
            notes=f"{self.concurrent_clients} parallele Clients mit asyncpg"
        )
    
    async def _test_async_selects(self) -> None:
        """Test: Asynchrone Selects mit parallelen Clients"""
        logger.info(f"Test: Async Selects ({self.concurrent_clients} Clients)")
        
        latencies = []
        latency_lock = asyncio.Lock()
        
        async def select_batch(user_ids: list[str]):
            """Liest einen Batch von Usern asynchron."""
            local_latencies = []
            
            async with self.async_pool.acquire() as conn:
                for user_id in user_ids:
                    start = time.perf_counter_ns()
                    
                    await conn.fetchrow(
                        "SELECT * FROM test_users WHERE user_id = $1",
                        user_id
                    )
                    
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
            
            tasks.append(select_batch(self.inserted_ids[start_idx:end_idx]))
        
        await asyncio.gather(*tasks)
        
        total_end = time.perf_counter_ns()
        total_duration_ms = ns_to_ms(total_end - total_start)
        
        self.record_result(
            test_name="PostgreSQL Async SELECT",
            operation_type="read",
            latencies_ms=latencies,
            total_operations=len(self.inserted_ids),
            total_duration_ms=total_duration_ms,
            is_async=True,
            concurrent_clients=self.concurrent_clients,
            notes=f"{self.concurrent_clients} parallele Clients mit asyncpg"
        )
