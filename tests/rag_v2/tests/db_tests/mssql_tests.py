"""
Microsoft SQL Server Performance Tests
=======================================

Performance-Tests für MSSQL als SQL-Datenbank im RAG-System.

WARUM TESTEN WIR DAS?
---------------------
MSSQL ist eine Enterprise-Grade SQL-Datenbank (Modul 4 & 5):
    - ACID-Transaktionen: Zuverlässige Datenintegrität
    - Columnstore Index: Analytische Queries
    - Full-Text Search: Integrierte Textsuche
    - JSON Support: Semi-strukturierte Daten (ab SQL Server 2016)
    - T-SQL: Erweiterte SQL-Funktionen

ERWARTUNGSHALTUNG (HYPOTHESE):
------------------------------
1. Batch-Inserts sind signifikant schneller als Single-Inserts
   
2. Clustered Index (Primary Key) liefert schnellste Lookups
   
3. Non-Clustered Index beschleunigt sekundäre Queries
   
4. P99 Latenz für indizierte SELECTs unter 10ms

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

# MSSQL-Treiber
try:
    import pymssql
    HAS_PYMSSQL = True
except ImportError:
    HAS_PYMSSQL = False

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import ns_to_ms

logger = logging.getLogger(__name__)


class MSSQLPerformanceTest(BasePerformanceTest):
    """
    Microsoft SQL Server Performance Tests.
    
    Dieser Test deckt folgende Szenarien ab:
    
    WRITE-TESTS (Szenario A):
        - Single Commits: Jedes INSERT mit eigenem COMMIT
        - Transactional Batch: Alle INSERTs in einer Transaktion
        - executemany: Batch-Insert
        - MERGE (Upsert): Insert or Update Pattern
    
    READ-TESTS (Szenario B):
        - Clustered Index Lookup (Primary Key)
        - Non-Clustered Index Query
        - Full Table Scan
        - TOP N Queries
    
    SPECIAL TESTS:
        - JSON Path Queries
        - LIKE Pattern Matching
        - Covering Index Tests
    """
    
    DATABASE_NAME = "MSSQL"
    DATABASE_CATEGORY = "SQL"
    
    TEST_DESCRIPTION = """
    Microsoft SQL Server Performance Tests
    
    WARUM: MSSQL ist eine Enterprise SQL-Datenbank mit
           erweiterten Features wie Columnstore und Full-Text Search.
    
    HYPOTHESE:
        - Transaktionsbatch ist signifikant schneller als Single Commits
        - Clustered Index bietet schnellste Lookups
        - Non-Clustered Index beschleunigt sekundäre Queries
        - P99 Latenz unter 10ms für indizierte SELECTs
    
    REFERENZ: Modul 4 (Query Paths), Modul 8 (SQL Performance)
    """
    
    def __init__(self, context: TestContext):
        """Initialisiert den MSSQL-Test."""
        super().__init__(context)
        
        if not HAS_PYMSSQL:
            raise ImportError(
                "pymssql nicht installiert. "
                "Installiere mit: pip install pymssql"
            )
        
        # MSSQL-Konfiguration
        db_config = self.config.get("databases", {}).get("mssql", {})
        self.host = db_config.get("host", "localhost")
        self.port = db_config.get("port", 1433)
        self.database = db_config.get("database", "rag_performance_test")
        self.user = db_config.get("user", "sa")
        self.password = db_config.get("password", "TestPassword123!")
        
        # Clients
        self.conn = None
        
        # Testdaten
        self.test_users: list[dict] = []
        self.inserted_ids: list[str] = []
    
    def setup(self) -> None:
        """Bereitet den MSSQL-Test vor."""
        logger.info(f"Verbinde zu MSSQL: {self.host}:{self.port}")
        
        # Erst ohne Datenbank verbinden, um diese zu erstellen
        self.conn = pymssql.connect(
            server=self.host,
            port=str(self.port),
            user=self.user,
            password=self.password,
            autocommit=True,
        )
        
        # Datenbank erstellen falls nicht vorhanden
        cursor = self.conn.cursor()
        cursor.execute(f"""
            IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{self.database}')
            BEGIN
                CREATE DATABASE {self.database}
            END
        """)
        cursor.close()
        self.conn.close()
        
        # Neu verbinden mit Datenbank
        self.conn = pymssql.connect(
            server=self.host,
            port=str(self.port),
            user=self.user,
            password=self.password,
            database=self.database,
            autocommit=False,
        )
        
        logger.info("✓ MSSQL-Verbindung hergestellt")
        
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
        cursor.execute("""
            IF OBJECT_ID('test_logs', 'U') IS NOT NULL DROP TABLE test_logs
        """)
        cursor.execute("""
            IF OBJECT_ID('test_users', 'U') IS NOT NULL DROP TABLE test_users
        """)
        
        # Users-Tabelle mit Clustered Primary Key
        cursor.execute("""
            CREATE TABLE test_users (
                user_id NVARCHAR(36) PRIMARY KEY CLUSTERED,
                username NVARCHAR(100) NOT NULL,
                email NVARCHAR(255) NOT NULL,
                full_name NVARCHAR(255),
                created_at DATETIME2 DEFAULT GETDATE(),
                is_active BIT DEFAULT 1,
                role NVARCHAR(50) DEFAULT 'user',
                unindexed_field NVARCHAR(100),
                json_data NVARCHAR(MAX)
            )
        """)
        
        # Non-Clustered Index auf email
        cursor.execute("""
            CREATE NONCLUSTERED INDEX idx_users_email ON test_users(email)
        """)
        
        # Non-Clustered Index auf role
        cursor.execute("""
            CREATE NONCLUSTERED INDEX idx_users_role ON test_users(role)
        """)
        
        # Logs-Tabelle
        cursor.execute("""
            CREATE TABLE test_logs (
                log_id INT IDENTITY(1,1) PRIMARY KEY,
                user_id NVARCHAR(36),
                action NVARCHAR(100),
                details NVARCHAR(MAX),
                timestamp DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (user_id) REFERENCES test_users(user_id)
            )
        """)
        
        # Index auf user_id + timestamp für JOIN
        cursor.execute("""
            CREATE NONCLUSTERED INDEX idx_logs_user_timestamp 
            ON test_logs(user_id, timestamp)
        """)
        
        self.conn.commit()
        cursor.close()
        
        logger.info("✓ Tabellen erstellt")
    
    def teardown(self) -> None:
        """Räumt nach dem Test auf."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("IF OBJECT_ID('test_logs', 'U') IS NOT NULL DROP TABLE test_logs")
                cursor.execute("IF OBJECT_ID('test_users', 'U') IS NOT NULL DROP TABLE test_users")
                self.conn.commit()
                cursor.close()
                self.conn.close()
                logger.info("✓ MSSQL-Verbindung geschlossen")
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
        """Führt alle MSSQL-Tests aus."""
        
        # =====================================================================
        # WRITE TESTS
        # =====================================================================
        logger.info("\n--- Write Performance Tests ---")
        
        self._test_single_commits()
        self._truncate_table()
        
        self._test_transactional_batch()
        self._truncate_table()
        
        self._test_executemany()
        
        # =====================================================================
        # READ TESTS
        # =====================================================================
        logger.info("\n--- Read Performance Tests ---")
        
        self._test_clustered_index_lookup()
        self._test_non_clustered_index_query()
        self._test_non_indexed_query()
        self._test_top_n_query()
        self._test_join_query()
        
        # =====================================================================
        # SPECIAL TESTS
        # =====================================================================
        logger.info("\n--- Special Tests ---")
        
        self._test_json_query()
        self._test_like_pattern()
        self._test_count_aggregation()
    
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
            test_name="MSSQL: Single Commits (1 INSERT = 1 COMMIT)",
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
            test_name="MSSQL: Transactional Batch (N INSERTs = 1 COMMIT)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_executemany(self) -> None:
        """Test: Batch-Insert mit executemany."""
        logger.info("Test: executemany (Batch Insert)")
        
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
            test_name="MSSQL: executemany (Batch Insert)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="write",
            total_operations=len(self.test_users),
            total_time_ns=total_time,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, Total: {ns_to_ms(total_time):.2f}ms")
    
    def _test_clustered_index_lookup(self) -> None:
        """Test: Clustered Index (Primary Key) Lookup."""
        logger.info("Test: Clustered Index Lookup (Primary Key)")
        
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
            test_name="MSSQL: Clustered Index Lookup (PK)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_non_clustered_index_query(self) -> None:
        """Test: Non-Clustered Index Query."""
        logger.info("Test: Non-Clustered Index Query (email)")
        
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
            test_name="MSSQL: Non-Clustered Index Query (email)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_non_indexed_query(self) -> None:
        """Test: Query auf nicht-indizierter Spalte."""
        logger.info("Test: Non-Indexed Query (Table Scan)")
        
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
            test_name="MSSQL: Non-Indexed Query (Table Scan)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_top_n_query(self) -> None:
        """Test: TOP N Query mit Order By."""
        logger.info("Test: TOP N Query")
        
        cursor = self.conn.cursor()
        latencies = []
        
        for i in range(min(500, self.num_operations)):
            start = time.perf_counter_ns()
            
            cursor.execute("""
                SELECT TOP 100 * FROM test_users 
                ORDER BY created_at DESC
            """)
            cursor.fetchall()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MSSQL: TOP N Query",
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
                INNER JOIN test_logs l ON u.user_id = l.user_id
                WHERE u.user_id = %s
            """, (user_id,))
            cursor.fetchall()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MSSQL: JOIN Query (users + logs)",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
    
    def _test_json_query(self) -> None:
        """Test: JSON Path Query."""
        logger.info("Test: JSON Path Query")
        
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
                SELECT user_id, JSON_VALUE(json_data, '$.preferences.theme') as theme
                FROM test_users 
                WHERE user_id = %s AND json_data IS NOT NULL
            """, (user_id,))
            cursor.fetchone()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MSSQL: JSON Path Query",
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
            
            cursor.execute("""
                SELECT TOP 10 * FROM test_users 
                WHERE email LIKE %s
            """, (f"%user_{i}%",))
            cursor.fetchall()
            
            latencies.append(time.perf_counter_ns() - start)
        
        cursor.close()
        
        result = self.metrics.calculate_from_latencies(
            test_name="MSSQL: LIKE Pattern Matching",
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
            test_name="MSSQL: COUNT Aggregation",
            database=self.DATABASE_NAME,
            category=self.DATABASE_CATEGORY,
            operation_type="read",
            latencies_ns=latencies,
        )
        self.results.append(result)
        logger.info(f"  → {result.ops_per_second:.2f} Ops/s, P99: {result.p99_latency_ms:.2f}ms")
