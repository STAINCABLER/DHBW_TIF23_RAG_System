#!/usr/bin/env python3
"""
RAG-System Datenbank Performance Tests - Haupt-Entry-Point
=============================================================

Dieses Script orchestriert alle Performance-Tests für das RAG-System.

VERWENDUNG:
-----------
    # Alle Tests ausführen
    python run_tests.py

    # Nur bestimmte Tests ausführen
    python run_tests.py --tests redis,mongo

    # Ohne Docker-Management (Container laufen bereits)
    python run_tests.py --no-docker

    # Eigene Konfigurationsdatei
    python run_tests.py --config custom_config.yaml

WORKFLOW:
---------
1. Konfiguration laden
2. Docker-Container starten (falls nicht --no-docker)
3. Tests ausführen:
   - Redis Tests
   - MongoDB Tests
   - PostgreSQL Tests
   - Vector Search Tests
4. Report generieren
5. Docker-Container stoppen

REFERENZ:
---------
- Anforderungen: anforderungen-tests.md
- Kursmaterialien: Modul 2, 4, 7, 8

Autor: RAG Performance Test Suite
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Sicherstellen, dass das tests-Verzeichnis im Python-Pfad ist
TESTS_DIR = Path(__file__).parent.resolve()
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import yaml

# Eigene Module importieren
from utils import (
    DockerManager,
    DataGenerator,
    MetricsCalculator,
    ReportGenerator,
)
from db_tests import (
    # SQL-Datenbanken
    PostgresPerformanceTest,
    MariaDBPerformanceTest,
    MySQLPerformanceTest,
    MSSQLPerformanceTest,
    # NoSQL/Document-Datenbanken
    RedisPerformanceTest,
    MongoPerformanceTest,
    CouchDBPerformanceTest,
    # Vektor-Datenbanken
    VectorPerformanceTest,
)
from db_tests.e2e_ingest_tests import E2EIngestPerformanceTest
from db_tests.base_test import TestContext

# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(config: dict) -> None:
    """Konfiguriert das Logging-System."""
    log_config = config.get("logging", {})
    report_config = config.get("reporting", {})
    log_level = getattr(logging, log_config.get("level", "INFO").upper())
    
    # Format
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # File Handler (optional)
    if log_config.get("file_logging", False):
        # Dynamischer Dateiname mit Timestamp (wie bei Reports)
        timestamp_format = report_config.get("timestamp_format", "%Y-%m-%d_%H-%M-%S")
        timestamp = datetime.now().strftime(timestamp_format)
        filename_pattern = log_config.get("filename_pattern", "log_{timestamp}.log")
        filename = filename_pattern.replace("{timestamp}", timestamp)
        
        output_dir = Path(__file__).parent / log_config.get("output_dir", "logs")
        output_dir.mkdir(parents=True, exist_ok=True)
        log_file = output_dir / filename
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

# =============================================================================
# Hauptprogramm
# =============================================================================

def load_config(config_path: Path) -> dict:
    """Lädt die Konfigurationsdatei."""
    if not config_path.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_arguments() -> argparse.Namespace:
    """Parst die Kommandozeilenargumente."""
    parser = argparse.ArgumentParser(
        description="RAG-System Datenbank Performance Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    python run_tests.py                     # Alle Tests
    python run_tests.py --tests redis       # Nur Redis
    python run_tests.py --no-docker         # Container laufen bereits
    python run_tests.py --tests vector      # Nur Vektorsuche
        """
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "config" / "test_config.yaml",
        help="Pfad zur Konfigurationsdatei (Standard: config/test_config.yaml)"
    )
    
    parser.add_argument(
        "--tests",
        type=str,
        default="all",
        help="Komma-separierte Liste der Tests: redis,mongo,postgres,vector,all (Standard: all)"
    )
    
    parser.add_argument(
        "--no-docker",
        action="store_true",
        help="Docker-Container nicht automatisch starten/stoppen"
    )
    
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Keinen Markdown-Report generieren"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführlichere Ausgabe (DEBUG-Level)"
    )
    
    return parser.parse_args()


def run_tests(
    config: dict,
    selected_tests: list[str],
    report_generator: ReportGenerator
) -> None:
    """
    Führt die ausgewählten Tests aus.
    
    Args:
        config: Geladene Konfiguration
        selected_tests: Liste der auszuführenden Tests
        report_generator: Report-Generator für Ergebnisse
    """
    import time
    
    # Gemeinsamen Kontext erstellen
    data_generator = DataGenerator(config)
    metrics_calculator = MetricsCalculator()
    
    context = TestContext(
        config=config,
        data_generator=data_generator,
        metrics_calculator=metrics_calculator,
    )
    
    # Test-Mapping (erweitert für alle Datenbanken)
    test_classes = {
        # SQL-Datenbanken
        "postgres": PostgresPerformanceTest,
        "mariadb": MariaDBPerformanceTest,
        "mysql": MySQLPerformanceTest,
        "mssql": MSSQLPerformanceTest,
        # NoSQL/Document-Datenbanken
        "redis": RedisPerformanceTest,
        "mongo": MongoPerformanceTest,
        "couchdb": CouchDBPerformanceTest,
        # Vektor-Datenbanken
        "vector": VectorPerformanceTest,
        # End-to-End Ingest-Tests
        "e2e": E2EIngestPerformanceTest,
    }
    
    # Gesamtlaufzeit und Laufzeiten pro Test
    total_start_time = time.time()
    test_durations = {}
    
    # Tests ausführen
    for test_name in selected_tests:
        if test_name not in test_classes:
            logger.warning(f"Unbekannter Test: {test_name}")
            continue
        
        test_class = test_classes[test_name]
        test_start_time = time.time()
        
        try:
            logger.info("\n" + "=" * 70)
            logger.info(f"Starte {test_name.upper()} Tests")
            logger.info("=" * 70)
            
            test = test_class(context)
            results = test.run_all_tests()
            
            # Testlaufzeit berechnen
            test_duration = time.time() - test_start_time
            test_durations[test_name] = test_duration
            logger.info(f"✓ {test_name.upper()} abgeschlossen in {test_duration:.2f}s ({len(results)} Tests)")
            
            # Ergebnisse zum Report hinzufügen
            for result in results:
                report_generator.add_result(result)
            
            # Vergleiche berechnen und hinzufügen
            _add_comparisons(test_name, results, metrics_calculator, report_generator)
            
        except ImportError as e:
            test_duration = time.time() - test_start_time
            test_durations[test_name] = test_duration
            logger.error(f"Abhängigkeit fehlt für {test_name}: {e}")
            report_generator.add_note(f"{test_name}: Test übersprungen - {e}")
        
        except Exception as e:
            test_duration = time.time() - test_start_time
            test_durations[test_name] = test_duration
            logger.exception(f"Fehler in {test_name} Tests: {e}")
            report_generator.add_note(f"{test_name}: Fehler - {e}")
    
    # Gesamtlaufzeit berechnen
    total_duration = time.time() - total_start_time
    
    # Laufzeiten loggen
    logger.info("\n" + "=" * 70)
    logger.info("Testlaufzeiten")
    logger.info("=" * 70)
    for test_name, duration in test_durations.items():
        logger.info(f"  {test_name.upper()}: {duration:.2f}s")
    logger.info("-" * 70)
    logger.info(f"  GESAMT: {total_duration:.2f}s")
    logger.info("=" * 70)
    
    # Laufzeiten zum Report hinzufügen
    report_generator.set_test_durations(test_durations, total_duration)
    
    # Cross-Database-Vergleiche hinzufügen (nach allen Tests)
    _add_cross_database_comparisons(report_generator, metrics_calculator)


def _add_comparisons(
    test_name: str,
    results: list,
    metrics: MetricsCalculator,
    report: ReportGenerator
) -> None:
    """Fügt intra-Datenbank-Vergleiche hinzu (innerhalb einer DB)."""
    if test_name == "redis":
        # Naive vs. Pipeline vergleichen (Write)
        naive_set = next((r for r in results if "Naive SET" in r.test_name), None)
        pipe_set = next((r for r in results if "Pipeline SET" in r.test_name), None)
        
        if naive_set and pipe_set:
            comparison = metrics.compare_results(naive_set, pipe_set)
            report.add_comparison("Redis: Naive SET vs. Pipeline SET", comparison)
        
        # Naive vs. Pipeline vergleichen (Read)
        naive_get = next((r for r in results if "Naive GET" in r.test_name), None)
        pipe_get = next((r for r in results if "Pipeline GET" in r.test_name), None)
        
        if naive_get and pipe_get:
            comparison = metrics.compare_results(naive_get, pipe_get)
            report.add_comparison("Redis: Naive GET vs. Pipeline GET", comparison)
        
        # Sync vs. Async vergleichen
        sync_set = next((r for r in results if "Naive SET" in r.test_name), None)
        async_set = next((r for r in results if "Async SET" in r.test_name), None)
        
        if sync_set and async_set:
            comparison = metrics.compare_results(sync_set, async_set)
            report.add_comparison("Redis: Sync SET vs. Async SET", comparison)
    
    elif test_name == "mongo":
        # Single vs. Bulk vergleichen (Write)
        single = next((r for r in results if "Single insert_one" in r.test_name), None)
        bulk = next((r for r in results if "Bulk insert_many" in r.test_name), None)
        
        if single and bulk:
            comparison = metrics.compare_results(single, bulk)
            report.add_comparison("MongoDB: Single vs. Bulk Insert", comparison)
        
        # Single vs. Batch vergleichen (Read)
        single_read = next((r for r in results if "Single find_one" in r.test_name), None)
        batch_read = next((r for r in results if "Batch find" in r.test_name), None)
        
        if single_read and batch_read:
            comparison = metrics.compare_results(single_read, batch_read)
            report.add_comparison("MongoDB: Single find_one vs. Batch find", comparison)
        
        # Sync vs. Async vergleichen
        sync_insert = next((r for r in results if "Single insert_one" in r.test_name and "Async" not in r.test_name), None)
        async_insert = next((r for r in results if "Async insert_one" in r.test_name), None)
        
        if sync_insert and async_insert:
            comparison = metrics.compare_results(sync_insert, async_insert)
            report.add_comparison("MongoDB: Sync vs. Async Insert", comparison)
    
    elif test_name == "postgres":
        # Single Commits vs. Transactional vergleichen
        single = next((r for r in results if "Single Commits" in r.test_name), None)
        batch = next((r for r in results if "Transactional Batch" in r.test_name), None)
        
        if single and batch:
            comparison = metrics.compare_results(single, batch)
            report.add_comparison("PostgreSQL: Single Commits vs. Transactional", comparison)
        
        # executemany vs. COPY vergleichen (falls vorhanden)
        executemany = next((r for r in results if "executemany" in r.test_name), None)
        copy = next((r for r in results if "COPY" in r.test_name), None)
        
        if executemany and copy:
            comparison = metrics.compare_results(executemany, copy)
            report.add_comparison("PostgreSQL: executemany vs. COPY", comparison)
    
    elif test_name == "mariadb":
        # MariaDB Single vs. Batch
        single = next((r for r in results if "Single Commits" in r.test_name), None)
        batch = next((r for r in results if "Transactional Batch" in r.test_name), None)
        
        if single and batch:
            comparison = metrics.compare_results(single, batch)
            report.add_comparison("MariaDB: Single Commits vs. Transactional", comparison)
    
    elif test_name == "mysql":
        # MySQL Single vs. Batch
        single = next((r for r in results if "Single Commits" in r.test_name), None)
        batch = next((r for r in results if "Transactional Batch" in r.test_name), None)
        
        if single and batch:
            comparison = metrics.compare_results(single, batch)
            report.add_comparison("MySQL: Single Commits vs. Transactional", comparison)
    
    elif test_name == "mssql":
        # MSSQL Single vs. Batch
        single = next((r for r in results if "Single Commits" in r.test_name), None)
        batch = next((r for r in results if "Transactional Batch" in r.test_name), None)
        
        if single and batch:
            comparison = metrics.compare_results(single, batch)
            report.add_comparison("MSSQL: Single Commits vs. Transactional", comparison)
    
    elif test_name == "couchdb":
        # CouchDB Single vs. Bulk
        single = next((r for r in results if "Single Document Insert" in r.test_name), None)
        bulk = next((r for r in results if "Bulk Insert" in r.test_name), None)
        
        if single and bulk:
            comparison = metrics.compare_results(single, bulk)
            report.add_comparison("CouchDB: Single vs. Bulk Insert", comparison)
    
    elif test_name == "vector":
        # pgvector-Native: KNN vs. ANN
        native_knn = next((r for r in results if "Native KNN" in r.test_name), None)
        native_ann = next((r for r in results if "Native ANN (HNSW)" in r.test_name and "Filtered" not in r.test_name), None)
        
        if native_knn and native_ann:
            comparison = metrics.compare_results(native_knn, native_ann)
            report.add_comparison("pgvector-Native: KNN (exakt) vs. ANN (HNSW)", comparison)
        
        # pgvector-Manual: KNN vs. ANN
        manual_knn = next((r for r in results if "Manual KNN" in r.test_name), None)
        manual_ann = next((r for r in results if "Manual ANN (HNSW)" in r.test_name and "Filtered" not in r.test_name), None)
        
        if manual_knn and manual_ann:
            comparison = metrics.compare_results(manual_knn, manual_ann)
            report.add_comparison("pgvector-Manual: KNN (exakt) vs. ANN (HNSW)", comparison)
        
        # Native vs. Manual (ANN)
        if native_ann and manual_ann:
            comparison = metrics.compare_results(native_ann, manual_ann)
            report.add_comparison("pgvector: Native vs. Manual (ANN/HNSW)", comparison)
        
        # ANN vs. Filtered ANN
        native_filtered = next((r for r in results if "Native Filtered ANN" in r.test_name), None)
        if native_ann and native_filtered:
            comparison = metrics.compare_results(native_ann, native_filtered)
            report.add_comparison("pgvector-Native: ANN vs. Filtered ANN", comparison)
        
        # pgvector vs. MongoDB Vector Search
        pg_ann = native_ann or manual_ann
        mongo_vector = next((r for r in results if "MongoDB Vector Search" in r.test_name), None)
        
        if pg_ann and mongo_vector:
            comparison = metrics.compare_results(mongo_vector, pg_ann)
            report.add_comparison("Vector Search: MongoDB vs. pgvector (ANN)", comparison)
    
    elif test_name == "e2e":
        # E2E Storage-Vergleiche: PostgreSQL vs. MongoDB vs. Redis (alle Kombinationen)
        pg_store = next((r for r in results if "Store PostgreSQL" in r.test_name or "Store Postgres" in r.test_name), None)
        mongo_store = next((r for r in results if "Store MongoDB" in r.test_name or "Store Mongo" in r.test_name), None)
        redis_store = next((r for r in results if "Store Redis" in r.test_name), None)
        
        if pg_store and mongo_store:
            comparison = metrics.compare_results(pg_store, mongo_store)
            report.add_comparison("E2E Storage: PostgreSQL vs. MongoDB", comparison)
        
        if pg_store and redis_store:
            comparison = metrics.compare_results(pg_store, redis_store)
            report.add_comparison("E2E Storage: PostgreSQL vs. Redis", comparison)
        
        if mongo_store and redis_store:
            comparison = metrics.compare_results(mongo_store, redis_store)
            report.add_comparison("E2E Storage: MongoDB vs. Redis", comparison)
        
        # E2E Search-Vergleiche (alle Kombinationen)
        pg_search = next((r for r in results if "Search PostgreSQL" in r.test_name or "Search Postgres" in r.test_name), None)
        mongo_search = next((r for r in results if "Search MongoDB" in r.test_name or "Search Mongo" in r.test_name), None)
        redis_search = next((r for r in results if "Search Redis" in r.test_name), None)
        
        if pg_search and mongo_search:
            comparison = metrics.compare_results(pg_search, mongo_search)
            report.add_comparison("E2E Search: PostgreSQL vs. MongoDB", comparison)
        
        if pg_search and redis_search:
            comparison = metrics.compare_results(pg_search, redis_search)
            report.add_comparison("E2E Search: PostgreSQL vs. Redis", comparison)
        
        if mongo_search and redis_search:
            comparison = metrics.compare_results(mongo_search, redis_search)
            report.add_comparison("E2E Search: MongoDB vs. Redis", comparison)


def _add_cross_database_comparisons(
    report: ReportGenerator,
    metrics: MetricsCalculator
) -> None:
    """
    Fügt Cross-Database-Vergleiche hinzu (zwischen verschiedenen DBs).
    
    Diese Funktion wird NACH allen Tests ausgeführt und vergleicht:
    - SQL-Datenbanken untereinander
    - NoSQL-Datenbanken untereinander
    - SQL vs. NoSQL
    - Vector-Search-Implementierungen
    """
    all_results = report.results
    
    if len(all_results) < 2:
        return
    
    # =========================================================================
    # SQL-Datenbanken: Batch Insert Vergleich
    # =========================================================================
    sql_batch_results = {}
    for r in all_results:
        if r.category == "SQL" and "Transactional Batch" in r.test_name:
            sql_batch_results[r.database] = r
    
    sql_dbs = list(sql_batch_results.keys())
    for i, db1 in enumerate(sql_dbs):
        for db2 in sql_dbs[i+1:]:
            comparison = metrics.compare_results(sql_batch_results[db1], sql_batch_results[db2])
            report.add_comparison(f"SQL Batch Insert: {db1} vs. {db2}", comparison)
    
    # =========================================================================
    # SQL-Datenbanken: Single Read Vergleich
    # =========================================================================
    sql_read_results = {}
    for r in all_results:
        if r.category == "SQL" and r.operation_type == "read" and "Single" in r.test_name:
            sql_read_results[r.database] = r
    
    sql_dbs = list(sql_read_results.keys())
    for i, db1 in enumerate(sql_dbs):
        for db2 in sql_dbs[i+1:]:
            comparison = metrics.compare_results(sql_read_results[db1], sql_read_results[db2])
            report.add_comparison(f"SQL Single Read: {db1} vs. {db2}", comparison)
    
    # =========================================================================
    # NoSQL-Datenbanken: Bulk/Pipeline Write Vergleich
    # =========================================================================
    nosql_bulk_results = {}
    for r in all_results:
        if r.category == "NoSQL/Document" and r.operation_type == "write":
            # Beste Write-Performance pro DB (Bulk/Pipeline)
            if "Bulk" in r.test_name or "Pipeline" in r.test_name or "insert_many" in r.test_name:
                if r.database not in nosql_bulk_results or r.ops_per_second > nosql_bulk_results[r.database].ops_per_second:
                    nosql_bulk_results[r.database] = r
    
    nosql_dbs = list(nosql_bulk_results.keys())
    for i, db1 in enumerate(nosql_dbs):
        for db2 in nosql_dbs[i+1:]:
            comparison = metrics.compare_results(nosql_bulk_results[db1], nosql_bulk_results[db2])
            report.add_comparison(f"NoSQL Bulk Write: {db1} vs. {db2}", comparison)
    
    # =========================================================================
    # NoSQL-Datenbanken: Single Read Vergleich
    # =========================================================================
    nosql_read_results = {}
    for r in all_results:
        if r.category == "NoSQL/Document" and r.operation_type == "read":
            if "Single" in r.test_name or "Naive" in r.test_name or "find_one" in r.test_name:
                if r.database not in nosql_read_results:
                    nosql_read_results[r.database] = r
    
    nosql_dbs = list(nosql_read_results.keys())
    for i, db1 in enumerate(nosql_dbs):
        for db2 in nosql_dbs[i+1:]:
            comparison = metrics.compare_results(nosql_read_results[db1], nosql_read_results[db2])
            report.add_comparison(f"NoSQL Single Read: {db1} vs. {db2}", comparison)
    
    # =========================================================================
    # Cross-Category: Beste SQL vs. Beste NoSQL (Write)
    # =========================================================================
    best_sql_write = None
    best_nosql_write = None
    
    for r in all_results:
        if r.operation_type == "write":
            if r.category == "SQL":
                if best_sql_write is None or r.ops_per_second > best_sql_write.ops_per_second:
                    best_sql_write = r
            elif r.category == "NoSQL/Document":
                if best_nosql_write is None or r.ops_per_second > best_nosql_write.ops_per_second:
                    best_nosql_write = r
    
    if best_sql_write and best_nosql_write:
        comparison = metrics.compare_results(best_sql_write, best_nosql_write)
        report.add_comparison(
            f"Cross-Category Write: Beste SQL ({best_sql_write.database}) vs. Beste NoSQL ({best_nosql_write.database})",
            comparison
        )
    
    # =========================================================================
    # Cross-Category: Beste SQL vs. Beste NoSQL (Read)
    # =========================================================================
    best_sql_read = None
    best_nosql_read = None
    
    for r in all_results:
        if r.operation_type == "read":
            if r.category == "SQL":
                if best_sql_read is None or r.ops_per_second > best_sql_read.ops_per_second:
                    best_sql_read = r
            elif r.category == "NoSQL/Document":
                if best_nosql_read is None or r.ops_per_second > best_nosql_read.ops_per_second:
                    best_nosql_read = r
    
    if best_sql_read and best_nosql_read:
        comparison = metrics.compare_results(best_sql_read, best_nosql_read)
        report.add_comparison(
            f"Cross-Category Read: Beste SQL ({best_sql_read.database}) vs. Beste NoSQL ({best_nosql_read.database})",
            comparison
        )
    
    # =========================================================================
    # Vector Search: Alle Implementierungen vergleichen
    # =========================================================================
    vector_results = {}
    for r in all_results:
        if r.operation_type == "vector_search":
            # Gruppiere nach Datenbank/Variante
            key = f"{r.database}:{r.test_name}"
            vector_results[key] = r
    
    # Finde beste ANN-Implementierung pro "Typ"
    vector_ann_results = {}
    for r in all_results:
        if r.operation_type == "vector_search" and "ANN" in r.test_name and "Filtered" not in r.test_name:
            db_key = r.database
            if "Native" in r.test_name:
                db_key = "pgvector-Native"
            elif "Manual" in r.test_name:
                db_key = "pgvector-Manual"
            elif "MongoDB" in r.test_name or r.database == "MongoDB":
                db_key = "MongoDB"
            vector_ann_results[db_key] = r
    
    vector_dbs = list(vector_ann_results.keys())
    for i, db1 in enumerate(vector_dbs):
        for db2 in vector_dbs[i+1:]:
            comparison = metrics.compare_results(vector_ann_results[db1], vector_ann_results[db2])
            report.add_comparison(f"Vector ANN Search: {db1} vs. {db2}", comparison)


def main():
    """Hauptfunktion."""
    # Argumente parsen
    args = parse_arguments()
    
    # Konfiguration laden
    config = load_config(args.config)
    
    # Logging einrichten
    if args.verbose:
        config.setdefault("logging", {})["level"] = "DEBUG"
    setup_logging(config)
    
    # Header ausgeben
    logger.info("=" * 70)
    logger.info("RAG-System Datenbank Performance Tests")
    logger.info("=" * 70)
    logger.info(f"Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Konfiguration: {args.config}")
    
    # Zu testende Datenbanken ermitteln
    if args.tests.lower() == "all":
        # Alle Datenbanken testen
        selected_tests = [
            # SQL-Datenbanken
            "postgres", "mariadb", "mysql", "mssql",
            # NoSQL/Document-Datenbanken
            "redis", "mongo", "couchdb",
            # Vektor-Datenbanken
            "vector"
        ]
    elif args.tests.lower() == "sql":
        # Nur SQL-Datenbanken
        selected_tests = ["postgres", "mariadb", "mysql", "mssql"]
    elif args.tests.lower() == "nosql":
        # Nur NoSQL-Datenbanken
        selected_tests = ["redis", "mongo", "couchdb"]
    else:
        selected_tests = [t.strip().lower() for t in args.tests.split(",")]
    
    logger.info(f"Ausgewählte Tests: {', '.join(selected_tests)}")
    
    # Base Path
    base_path = Path(__file__).parent
    
    # Report Generator initialisieren
    report_generator = ReportGenerator(config, base_path)
    
    # Docker Manager initialisieren
    docker_manager = DockerManager(config, base_path)
    
    try:
        # Docker-Container starten (falls gewünscht)
        if not args.no_docker:
            logger.info("\n" + "-" * 70)
            logger.info("Starte Docker-Infrastruktur...")
            logger.info("-" * 70)
            docker_manager.start_containers()
        else:
            logger.info("Docker-Management übersprungen (--no-docker)")
        
        # Tests ausführen
        run_tests(config, selected_tests, report_generator)
        
        # Report generieren
        if not args.no_report:
            logger.info("\n" + "-" * 70)
            logger.info("Generiere Report...")
            logger.info("-" * 70)
            report_path = report_generator.generate()
            logger.info(f"✓ Report gespeichert: {report_path}")
        
        logger.info("\n" + "=" * 70)
        logger.info("Alle Tests erfolgreich abgeschlossen!")
        logger.info("=" * 70)
        
    except KeyboardInterrupt:
        logger.warning("\nTests durch Benutzer abgebrochen!")
    
    except Exception as e:
        logger.exception(f"Kritischer Fehler: {e}")
        sys.exit(1)
    
    finally:
        # Docker-Container stoppen (falls gewünscht)
        if not args.no_docker:
            logger.info("\n" + "-" * 70)
            logger.info("Stoppe Docker-Infrastruktur...")
            logger.info("-" * 70)
            docker_manager.stop_containers()


if __name__ == "__main__":
    main()
