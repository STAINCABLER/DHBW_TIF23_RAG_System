"""
MariaDB Performance Tests
==========================

Performance-Tests für MariaDB als SQL-Datenbank im RAG-System.

WARUM TESTEN WIR DAS?
---------------------
MariaDB ist ein MySQL-kompatibler Fork mit zusätzlichen Features (Modul 4 & 5):
    - MySQL-Kompatibilität: Drop-in Replacement für MySQL
    - InnoDB Engine: ACID-Transaktionen
    - Galera Cluster: Hohe Verfügbarkeit
    - JSON-Support: Semi-strukturierte Daten

ERWARTUNGSHALTUNG (HYPOTHESE):
------------------------------
1. Transaktionsbatch ist 50-100x schneller als einzelne Commits
   (Grund: WAL-Schreibvorgänge und fsync werden gebündelt)
   
2. Indizierte Queries sind 10-100x schneller als ohne Index
   (Grund: B-Tree Index vs. Full Table Scan)
   
3. P99 Latenz für SELECT mit Index sollte unter 5ms liegen

4. Prepared Statements sind schneller als normale Queries
   (Grund: Query-Parsing wird eingespart)

REFERENZ:
---------
- Modul 4: Query Paths bestimmen die Systemkosten
- Modul 8: Performance-Myth-Busting

Autor: RAG Performance Test Suite
"""

import time
import asyncio
import logging
from typing import Optional

# MariaDB/MySQL-Treiber
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    HAS_MYSQL_CONNECTOR = True
except ImportError:
    HAS_MYSQL_CONNECTOR = False

try:
    import mariadb
    HAS_MARIADB = True
except ImportError:
    HAS_MARIADB = False

try:
    import aiomysql
    HAS_AIOMYSQL = True
except ImportError:
    HAS_AIOMYSQL = False

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import ns_to_ms

logger = logging.getLogger(__name__)


class MariaDBPerformanceTest(BasePerformanceTest):
    """
    MariaDB Performance Tests - Synchron und Asynchron.
    
    Dieser Test deckt folgende Szenarien ab:
    
    WRITE-TESTS (Szenario A):
        - Single Commits: Jedes INSERT mit eigenem COMMIT (Baseline)
        - Transactional Batch: Alle INSERTs in einer Transaktion (optimiert)
        - executemany: Batch-Insert mit Prepared Statement
        - LOAD DATA: Bulk-Insert (wenn verfügbar)
    
    READ-TESTS (Szenario B):
        - Simple SELECT: Abruf per Primary Key
        - Filtered SELECT: Query mit WHERE-Clause
        - JOIN Query: Verknüpfung mehrerer Tabellen
        - Full Table Scan: Ohne Index (für Vergleich)
    
    INDEX-TESTS:
        - Mit Index: SELECT auf indizierter Spalte
        - Ohne Index: SELECT auf nicht-indizierter Spalte
    
    PREPARED STATEMENT TESTS:
        - Prepared vs. Non-Prepared Queries
    """
    
    DATABASE_NAME = "MariaDB"
    DATABASE_CATEGORY = "SQL"
    
    TEST_DESCRIPTION = """
    MariaDB SQL-Datenbank Performance Tests
    
    WARUM: MariaDB ist ein MySQL-kompatibler SQL-Server mit
           erweiterten Features und besserer Performance.
    
    HYPOTHESE:
        - Transaktionsbatch ist 50-100x schneller als Single Commits
        - Indizierte Queries sind 10-100x schneller
        - Prepared Statements beschleunigen wiederholte Queries
        - P99 Latenz unter 5ms für indizierte SELECTs
    
    REFERENZ: Modul 4 (Query Paths), Modul 8 (SQL Performance)
    """
    
    def __init__(self, context: TestContext):
        """Initialisiert den MariaDB-Test."""
        super().__init__(context)
        
        if not HAS_MYSQL_CONNECTOR and not HAS_MARIADB:
            raise ImportError(
                "Kein MariaDB/MySQL-Treiber installiert. "
                "Installiere mit: pip install mysql-connector-python oder pip install mariadb"
            )
        
        # MariaDB-Konfiguration
        db_config = self.config.get("databases", {}).get("mariadb", {})
        self.host = db_config.get("host", "localhost")
        self.port = db_config.get("port", 3306)
        self.database = db_config.get("database", "rag_performance_test")
        self.user = db_config.get("user", "testuser")
        self.password = db_config.get("password", "testpass")
        
        # Clients
        self.conn = None
        self.async_pool = None
        
        # Testdaten
        self.test_users: list[dict] = []
        self.inserted_ids: list[str] = []
    
    def setup(self) -> None:
        """
        Bereitet den MariaDB-Test vor.
        
        - Verbindung herstellen
        - Tabellen erstellen
        - Indizes anlegen
        - Testdaten generieren
        """
        logger.info(f"Verbinde zu MariaDB: {self.host}:{self.port}")
        
        # Verbindung mit mysql-connector
        if HAS_MYSQL_CONNECTOR:
            self.conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=False,
                connection_timeout=10,
            )
        elif HAS_MARIADB:
            self.conn = mariadb.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=False,
            )
        
        logger.info("✓ MariaDB-Verbindung hergestellt")
        
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
        cursor = self.conn.cursor()
        
        # Alte Tabellen löschen
        cursor.execute("DROP TABLE IF EXISTS test_logs")
        cursor.execute("DROP TABLE IF EXISTS test_users")
        
        # Users-Tabelle
        cursor.execute("""
            CREATE TABLE test_users (
                user_id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                role VARCHAR(50) DEFAULT 'user',
                unindexed_field VARCHAR(100)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # Index auf email
        cursor.execute("""
            CREATE INDEX idx_users_email ON test_users(email)
        """)
        
        # Index auf role
        cursor.execute("""
            CREATE INDEX idx_users_role ON test_users(role)
        """)
        
        # Logs-Tabelle (für JOIN-Tests)
        cursor.execute("""
            CREATE TABLE test_logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(36),
                action VARCHAR(100),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES test_users(user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        self.conn.commit()
        cursor.close()
        
        logger.info("✓ Tabellen erstellt")
    
    def teardown(self) -> None:
        """Räumt nach dem Test auf."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS test_logs")
                cursor.execute("DROP TABLE IF EXISTS test_users")
                self.conn.commit()
                cursor.close()
                self.conn.close()
                logger.info("✓ MariaDB-Verbindung geschlossen")
            except Exception as e:
                logger.warning(f"Fehler beim Schließen: {e}")
        
        self.test_users.clear()
        self.inserted_ids.clear()
    
    def warmup(self) -> None:
        """Führt Warmup-Operationen durch."""
        cursor = self.conn.cursor()
        
        for i in range(min(self.warmup_operations, 100)):
            cursor.execute(
                "INSERT INTO test_users (user_id, username, email) VALUES (%s, %s, %s)",
                (f"warmup_{i}", f"warmup_user_{i}", f"warmup_{i}@test.com")
            )
        self.conn.commit()
        
        # Lesen
        cursor.execute("SELECT * FROM test_users WHERE user_id LIKE 'warmup_%'")
        cursor.fetchall()
        
        # Löschen
        cursor.execute("DELETE FROM test_users WHERE user_id LIKE 'warmup_%'")
        self.conn.commit()
        cursor.close()
    
    def _run_tests(self) -> None:
        """Führt alle MariaDB-Tests aus."""
        
        # =====================================================================
        # WRITE TESTS
        # =====================================================================
        logger.info("\n--- Write Performance Tests ---")
        
        # Test 1: Single Commits (Baseline)
        self._test_single_commits()
        
        # Tabelle leeren für nächsten Test
        self._truncate_table()
        
        # Test 2: Transactional Batch
        self._test_transactional_batch()
        
        # Tabelle leeren
        self._truncate_table()
        
        # Test 3: executemany (Prepared Statement Batch)
        self._test_executemany()
        
        # =====================================================================
        # READ TESTS
        # =====================================================================
        logger.info("\n--- Read Performance Tests ---")
        
        # Test 4: Primary Key Lookup
        self._test_pk_lookup()
        
        # Test 5: Indexed Column Query
        self._test_indexed_query()
        
        # Test 6: Non-Indexed Column Query
        self._test_non_indexed_query()
        
        # Test 7: Range Query mit Index
        self._test_range_query()
        
        # Test 8: JOIN Query
        self._test_join_query()
        
        # =====================================================================
        # ASYNC TESTS (falls verfügbar)
        # =====================================================================
        if HAS_AIOMYSQL:
            logger.info("\n--- Async Performance Tests ---")
            asyncio.run(self._run_async_tests())
    
    def _truncate_table(self) -> None:
        """Leert die Test-Tabelle."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM test_logs")
        cursor.execute("DELETE FROM test_users")
        self.conn.commit()
        cursor.close()
        self.inserted_ids.clear()
    
    def _test_single_commits(self) -> None:
        """Test: Einzelne INSERTs mit jeweils eigenem COMMIT."""
        logger.info("Test: Single Commits (1 INSERT = 1 COMMIT)")
        
        cursor = self.conn.cursor()
        latencies = []
        
        for user in self.test_users:
            start = time.perf_counter_ns()
            
            cursor.execute(
                """INSERT INTO test_users 
                   (user_id, username, email, full_name, role, unindexed_field)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user['user_id'], user['username'], user['email'],
                 user['full_name'], user['role'], user.get('unindexed_field', ''))
            )
            self.conn.commit()
            
            latencies.append(time.perf_counter_ns() - start)
            self.inserted_ids.append(user['user_id'])
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MariaDB: Single Commits (1 INSERT = 1 COMMIT)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_transactional_batch(self) -> None:
        """Test: Alle INSERTs in einer Transaktion."""
        logger.info("Test: Transactional Batch (N INSERTs = 1 COMMIT)")
        
        cursor = self.conn.cursor()
        latencies = []
        
        start = time.perf_counter_ns()
        
        for user in self.test_users:
            op_start = time.perf_counter_ns()
            
            cursor.execute(
                """INSERT INTO test_users 
                   (user_id, username, email, full_name, role, unindexed_field)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user['user_id'], user['username'], user['email'],
                 user['full_name'], user['role'], user.get('unindexed_field', ''))
            )
            
            latencies.append(time.perf_counter_ns() - op_start)
            self.inserted_ids.append(user['user_id'])
        
        self.conn.commit()
        total_time = time.perf_counter_ns() - start
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MariaDB: Transactional Batch (N INSERTs = 1 COMMIT)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_executemany(self) -> None:
        """Test: Batch-Insert mit executemany."""
        logger.info("Test: executemany (Prepared Statement Batch)")
        
        cursor = self.conn.cursor()
        
        # Daten vorbereiten
        data = [
            (user['user_id'], user['username'], user['email'],
             user['full_name'], user['role'], user.get('unindexed_field', ''))
            for user in self.test_users
        ]
        
        start = time.perf_counter_ns()
        
        cursor.executemany(
            """INSERT INTO test_users 
               (user_id, username, email, full_name, role, unindexed_field)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            data
        )
        self.conn.commit()
        
        total_time = time.perf_counter_ns() - start
        
        cursor.close()
        self.inserted_ids.extend([user['user_id'] for user in self.test_users])
        
        result = self.metrics.calculate_from_total_time(
            test_name="MariaDB: executemany (Prepared Statement Batch)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            total_operations=len(self.test_users),
            total_time_ns=total_time,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, Total: {ns_to_ms(total_time):.2f}ms")
    
    def _test_pk_lookup(self) -> None:
        """Test: Primary Key Lookup."""
        logger.info("Test: Primary Key Lookup")
        
        cursor = self.conn.cursor()
        latencies = []
        
        for user_id in self.inserted_ids[:self.num_operations]:
            start = time.perf_counter_ns()
            
            cursor.execute(
                "SELECT * FROM test_users WHERE user_id = %s",
                (user_id,)
            )
            cursor.fetchone()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MariaDB: Primary Key Lookup",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_indexed_query(self) -> None:
        """Test: Query auf indizierter Spalte (email)."""
        logger.info("Test: Indexed Column Query (email)")
        
        cursor = self.conn.cursor()
        latencies = []
        
        for user in self.test_users[:min(1000, self.num_operations)]:
            start = time.perf_counter_ns()
            
            cursor.execute(
                "SELECT * FROM test_users WHERE email = %s",
                (user['email'],)
            )
            cursor.fetchall()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MariaDB: Indexed Column Query (email)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_non_indexed_query(self) -> None:
        """Test: Query auf nicht-indizierter Spalte."""
        logger.info("Test: Non-Indexed Column Query (Full Table Scan)")
        
        cursor = self.conn.cursor()
        latencies = []
        
        # Nur wenige Queries, da langsam
        for i in range(min(100, len(self.test_users))):
            start = time.perf_counter_ns()
            
            cursor.execute(
                "SELECT * FROM test_users WHERE unindexed_field = %s",
                (f"field_{i}",)
            )
            cursor.fetchall()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MariaDB: Non-Indexed Query (Full Table Scan)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_range_query(self) -> None:
        """Test: Range Query mit Index."""
        logger.info("Test: Range Query mit Index (role)")
        
        cursor = self.conn.cursor()
        latencies = []
        
        roles = ['user', 'admin', 'moderator']
        
        for i in range(min(1000, self.num_operations)):
            role = roles[i % len(roles)]
            
            start = time.perf_counter_ns()
            
            cursor.execute(
                "SELECT * FROM test_users WHERE role = %s LIMIT 100",
                (role,)
            )
            cursor.fetchall()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MariaDB: Range Query mit Index (role)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_join_query(self) -> None:
        """Test: JOIN Query zwischen zwei Tabellen."""
        logger.info("Test: JOIN Query (users + logs)")
        
        cursor = self.conn.cursor()
        
        # Erst Log-Einträge erstellen
        logger.info("  → Erstelle Log-Einträge für JOIN-Test...")
        for i, user_id in enumerate(self.inserted_ids[:1000]):
            cursor.execute(
                "INSERT INTO test_logs (user_id, action) VALUES (%s, %s)",
                (user_id, f"action_{i}")
            )
        self.conn.commit()
        
        latencies = []
        
        for user_id in self.inserted_ids[:min(500, len(self.inserted_ids))]:
            start = time.perf_counter_ns()
            
            cursor.execute("""
                SELECT u.*, l.action, l.timestamp 
                FROM test_users u
                JOIN test_logs l ON u.user_id = l.user_id
                WHERE u.user_id = %s
            """, (user_id,))
            cursor.fetchall()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MariaDB: JOIN Query (users + logs)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    async def _run_async_tests(self) -> None:
        """Führt asynchrone Tests aus."""
        logger.info("Starte asynchrone MariaDB-Tests...")
        
        # Pool erstellen
        pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            db=self.database,
            user=self.user,
            password=self.password,
            minsize=5,
            maxsize=20,
        )
        
        try:
            await self._async_concurrent_reads(pool)
            await self._async_concurrent_writes(pool)
        finally:
            pool.close()
            await pool.wait_closed()
    
    async def _async_concurrent_reads(self, pool) -> None:
        """Test: Parallele asynchrone Lesevorgänge."""
        logger.info(f"Test: Async Concurrent Reads ({self.concurrent_clients} Clients)")
        
        async def single_read(user_id: str) -> int:
            start = time.perf_counter_ns()
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT * FROM test_users WHERE user_id = %s",
                        (user_id,)
                    )
                    await cur.fetchone()
            return time.perf_counter_ns() - start
        
        # Parallele Ausführung
        tasks = [
            single_read(self.inserted_ids[i % len(self.inserted_ids)])
            for i in range(min(1000, self.num_operations))
        ]
        
        latencies = await asyncio.gather(*tasks)
        
        result = self.metrics.calculate_from_latencies(
            test_name=f"MariaDB: Async Concurrent Reads ({self.concurrent_clients} Clients)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=list(latencies),
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    async def _async_concurrent_writes(self, pool) -> None:
        """Test: Parallele asynchrone Schreibvorgänge."""
        logger.info(f"Test: Async Concurrent Writes ({self.concurrent_clients} Clients)")
        
        async def single_write(i: int) -> int:
            start = time.perf_counter_ns()
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """INSERT INTO test_users 
                           (user_id, username, email) 
                           VALUES (%s, %s, %s)
                           ON DUPLICATE KEY UPDATE username = VALUES(username)""",
                        (f"async_{i}", f"async_user_{i}", f"async_{i}@test.com")
                    )
                await conn.commit()
            return time.perf_counter_ns() - start
        
        tasks = [single_write(i) for i in range(min(1000, self.num_operations))]
        latencies = await asyncio.gather(*tasks)
        
        result = self.metrics.calculate_from_latencies(
            test_name=f"MariaDB: Async Concurrent Writes ({self.concurrent_clients} Clients)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=list(latencies),
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
