"""
MySQL Performance Tests
========================

Performance-Tests für MySQL als SQL-Datenbank im RAG-System.

WARUM TESTEN WIR DAS?
---------------------
MySQL ist eine der am weitesten verbreiteten SQL-Datenbanken (Modul 4 & 5):
    - InnoDB Engine: ACID-Transaktionen mit Row-Level Locking
    - B-Tree Indizes: Effiziente Suche
    - Replication: Master-Slave für Read-Scaling
    - JSON Support: Semi-strukturierte Daten (ab MySQL 5.7)

ERWARTUNGSHALTUNG (HYPOTHESE):
------------------------------
1. Transaktionsbatch ist 50-100x schneller als einzelne Commits
   (Grund: Reduced fsync und WAL-Overhead)
   
2. InnoDB Buffer Pool Cache beschleunigt wiederholte Reads
   
3. Prepared Statements sind schneller bei wiederholten Queries
   
4. P99 Latenz für indizierte SELECTs unter 5ms

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

# MySQL-Treiber
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    HAS_MYSQL_CONNECTOR = True
except ImportError:
    HAS_MYSQL_CONNECTOR = False

try:
    import aiomysql
    HAS_AIOMYSQL = True
except ImportError:
    HAS_AIOMYSQL = False

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import ns_to_ms

logger = logging.getLogger(__name__)


class MySQLPerformanceTest(BasePerformanceTest):
    """
    MySQL Performance Tests - Synchron und Asynchron.
    
    Dieser Test deckt folgende Szenarien ab:
    
    WRITE-TESTS (Szenario A):
        - Single Commits: Jedes INSERT mit eigenem COMMIT
        - Transactional Batch: Alle INSERTs in einer Transaktion
        - executemany: Batch-Insert mit Prepared Statement
        - INSERT ... ON DUPLICATE KEY UPDATE: Upsert-Pattern
    
    READ-TESTS (Szenario B):
        - Primary Key Lookup
        - Secondary Index Query
        - Full Table Scan (für Vergleich)
        - COUNT/Aggregation Queries
    
    SPECIAL TESTS:
        - Buffer Pool Hit Rate
        - Prepared Statement Cache
    """
    
    DATABASE_NAME = "MySQL"
    DATABASE_CATEGORY = "SQL"
    
    TEST_DESCRIPTION = """
    MySQL SQL-Datenbank Performance Tests
    
    WARUM: MySQL ist die weltweit am meisten verwendete 
           Open-Source SQL-Datenbank.
    
    HYPOTHESE:
        - Transaktionsbatch ist 50-100x schneller als Single Commits
        - InnoDB Buffer Pool beschleunigt Reads signifikant
        - Prepared Statements reduzieren Parse-Overhead
        - P99 Latenz unter 5ms für indizierte SELECTs
    
    REFERENZ: Modul 4 (Query Paths), Modul 8 (SQL Performance)
    """
    
    def __init__(self, context: TestContext):
        """Initialisiert den MySQL-Test."""
        super().__init__(context)
        
        if not HAS_MYSQL_CONNECTOR:
            raise ImportError(
                "mysql-connector-python nicht installiert. "
                "Installiere mit: pip install mysql-connector-python"
            )
        
        # MySQL-Konfiguration
        db_config = self.config.get("databases", {}).get("mysql", {})
        self.host = db_config.get("host", "localhost")
        self.port = db_config.get("port", 3307)
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
        """Bereitet den MySQL-Test vor."""
        logger.info(f"Verbinde zu MySQL: {self.host}:{self.port}")
        
        self.conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            autocommit=False,
            connection_timeout=10,
            use_pure=True,  # Pure Python für Kompatibilität
        )
        
        logger.info("✓ MySQL-Verbindung hergestellt")
        
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
        
        # Users-Tabelle mit verschiedenen Indizes
        cursor.execute("""
            CREATE TABLE test_users (
                user_id VARCHAR(36) PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                role VARCHAR(50) DEFAULT 'user',
                unindexed_field VARCHAR(100),
                json_data JSON,
                INDEX idx_email (email),
                INDEX idx_role (role),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        
        # Logs-Tabelle
        cursor.execute("""
            CREATE TABLE test_logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(36),
                action VARCHAR(100),
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES test_users(user_id),
                INDEX idx_user_timestamp (user_id, timestamp)
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
                logger.info("✓ MySQL-Verbindung geschlossen")
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
        
        cursor.execute("SELECT * FROM test_users WHERE user_id LIKE 'warmup_%'")
        cursor.fetchall()
        
        cursor.execute("DELETE FROM test_users WHERE user_id LIKE 'warmup_%'")
        self.conn.commit()
        cursor.close()
    
    def _run_tests(self) -> None:
        """Führt alle MySQL-Tests aus."""
        
        # =====================================================================
        # WRITE TESTS
        # =====================================================================
        logger.info("\n--- Write Performance Tests ---")
        
        self._test_single_commits()
        self._truncate_table()
        
        self._test_transactional_batch()
        self._truncate_table()
        
        self._test_executemany()
        self._truncate_table()
        
        self._test_insert_ignore()
        
        # =====================================================================
        # READ TESTS
        # =====================================================================
        logger.info("\n--- Read Performance Tests ---")
        
        self._test_pk_lookup()
        self._test_indexed_query()
        self._test_non_indexed_query()
        self._test_range_query()
        self._test_count_aggregation()
        self._test_join_query()
        
        # =====================================================================
        # SPECIAL TESTS
        # =====================================================================
        logger.info("\n--- Special Tests ---")
        
        self._test_json_query()
        self._test_like_pattern()
        
        # =====================================================================
        # ASYNC TESTS
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
            test_name="MySQL: Single Commits (1 INSERT = 1 COMMIT)",
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
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MySQL: Transactional Batch (N INSERTs = 1 COMMIT)",
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
            test_name="MySQL: executemany (Prepared Statement Batch)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            total_operations=len(self.test_users),
            total_time_ns=total_time,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, Total: {ns_to_ms(total_time):.2f}ms")
    
    def _test_insert_ignore(self) -> None:
        """Test: INSERT IGNORE für Duplikate."""
        logger.info("Test: INSERT IGNORE (Skip Duplicates)")
        
        cursor = self.conn.cursor()
        
        # Erst normale Inserts
        for user in self.test_users[:1000]:
            cursor.execute(
                """INSERT INTO test_users 
                   (user_id, username, email, full_name, role)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user['user_id'], user['username'], user['email'],
                 user['full_name'], user['role'])
            )
        self.conn.commit()
        
        # Dann INSERT IGNORE mit Duplikaten
        latencies = []
        
        for user in self.test_users[:1000]:
            start = time.perf_counter_ns()
            
            cursor.execute(
                """INSERT IGNORE INTO test_users 
                   (user_id, username, email, full_name, role)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user['user_id'], f"updated_{user['username']}", user['email'],
                 user['full_name'], user['role'])
            )
            
            latencies.append(time.perf_counter_ns() - start)
        
        self.conn.commit()
        cursor.close()
        
        self.inserted_ids.extend([user['user_id'] for user in self.test_users[:1000]])
        
        result = self.metrics.calculate_from_latencies(
            test_name="MySQL: INSERT IGNORE (Skip Duplicates)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
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
            test_name="MySQL: Primary Key Lookup",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_indexed_query(self) -> None:
        """Test: Query auf indizierter Spalte."""
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
            test_name="MySQL: Indexed Column Query (email)",
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
            test_name="MySQL: Non-Indexed Query (Full Table Scan)",
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
            test_name="MySQL: Range Query mit Index (role)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_count_aggregation(self) -> None:
        """Test: COUNT Aggregation."""
        logger.info("Test: COUNT Aggregation")
        
        cursor = self.conn.cursor()
        latencies = []
        
        for i in range(100):
            start = time.perf_counter_ns()
            
            cursor.execute("SELECT COUNT(*) FROM test_users WHERE role = %s", ('user',))
            cursor.fetchone()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MySQL: COUNT Aggregation",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_join_query(self) -> None:
        """Test: JOIN Query."""
        logger.info("Test: JOIN Query (users + logs)")
        
        cursor = self.conn.cursor()
        
        # Log-Einträge erstellen
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
            test_name="MySQL: JOIN Query (users + logs)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_json_query(self) -> None:
        """Test: JSON Column Query (MySQL 5.7+)."""
        logger.info("Test: JSON Column Query")
        
        cursor = self.conn.cursor()
        
        # JSON Daten einfügen
        for i, user_id in enumerate(self.inserted_ids[:100]):
            cursor.execute(
                "UPDATE test_users SET json_data = %s WHERE user_id = %s",
                ('{"preferences": {"theme": "dark", "notifications": true}}', user_id)
            )
        self.conn.commit()
        
        latencies = []
        
        for user_id in self.inserted_ids[:100]:
            start = time.perf_counter_ns()
            
            cursor.execute("""
                SELECT user_id, JSON_EXTRACT(json_data, '$.preferences.theme') as theme
                FROM test_users 
                WHERE user_id = %s AND json_data IS NOT NULL
            """, (user_id,))
            cursor.fetchone()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MySQL: JSON Column Query",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_like_pattern(self) -> None:
        """Test: LIKE Pattern Matching."""
        logger.info("Test: LIKE Pattern Matching")
        
        cursor = self.conn.cursor()
        latencies = []
        
        for i in range(100):
            start = time.perf_counter_ns()
            
            cursor.execute(
                "SELECT * FROM test_users WHERE email LIKE %s LIMIT 10",
                (f"%user_{i}%",)
            )
            cursor.fetchall()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MySQL: LIKE Pattern Matching",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    async def _run_async_tests(self) -> None:
        """Führt asynchrone Tests aus."""
        logger.info("Starte asynchrone MySQL-Tests...")
        
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
        
        tasks = [
            single_read(self.inserted_ids[i % len(self.inserted_ids)])
            for i in range(min(1000, self.num_operations))
        ]
        
        latencies = await asyncio.gather(*tasks)
        
        result = self.metrics.calculate_from_latencies(
            test_name=f"MySQL: Async Concurrent Reads ({self.concurrent_clients} Clients)",
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
            test_name=f"MySQL: Async Concurrent Writes ({self.concurrent_clients} Clients)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=list(latencies),
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
