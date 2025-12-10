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
    RedisPerformanceTest,
    MongoPerformanceTest,
    PostgresPerformanceTest,
    VectorPerformanceTest,
)
from db_tests.base_test import TestContext

# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(config: dict) -> None:
    """Konfiguriert das Logging-System."""
    log_config = config.get("logging", {})
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
        log_file = Path(__file__).parent / log_config.get("log_file", "logs/test_run.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
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
    # Gemeinsamen Kontext erstellen
    data_generator = DataGenerator(config)
    metrics_calculator = MetricsCalculator()
    
    context = TestContext(
        config=config,
        data_generator=data_generator,
        metrics_calculator=metrics_calculator,
    )
    
    # Test-Mapping
    test_classes = {
        "redis": RedisPerformanceTest,
        "mongo": MongoPerformanceTest,
        "postgres": PostgresPerformanceTest,
        "vector": VectorPerformanceTest,
    }
    
    # Tests ausführen
    for test_name in selected_tests:
        if test_name not in test_classes:
            logger.warning(f"Unbekannter Test: {test_name}")
            continue
        
        test_class = test_classes[test_name]
        
        try:
            logger.info("\n" + "=" * 70)
            logger.info(f"Starte {test_name.upper()} Tests")
            logger.info("=" * 70)
            
            test = test_class(context)
            results = test.run_all_tests()
            
            # Ergebnisse zum Report hinzufügen
            for result in results:
                report_generator.add_result(result)
            
            # Vergleiche berechnen und hinzufügen
            _add_comparisons(test_name, results, metrics_calculator, report_generator)
            
        except ImportError as e:
            logger.error(f"Abhängigkeit fehlt für {test_name}: {e}")
            report_generator.add_note(f"{test_name}: Test übersprungen - {e}")
        
        except Exception as e:
            logger.exception(f"Fehler in {test_name} Tests: {e}")
            report_generator.add_note(f"{test_name}: Fehler - {e}")


def _add_comparisons(
    test_name: str,
    results: list,
    metrics: MetricsCalculator,
    report: ReportGenerator
) -> None:
    """Fügt Vergleiche zwischen Tests hinzu."""
    if test_name == "redis":
        # Naive vs. Pipeline vergleichen
        naive_set = next((r for r in results if "Naive SET" in r.test_name), None)
        pipe_set = next((r for r in results if "Pipeline SET" in r.test_name), None)
        
        if naive_set and pipe_set:
            comparison = metrics.compare_results(naive_set, pipe_set)
            report.add_comparison("Redis: Naive SET vs. Pipeline SET", comparison)
    
    elif test_name == "mongo":
        # Single vs. Bulk vergleichen
        single = next((r for r in results if "Single insert_one" in r.test_name), None)
        bulk = next((r for r in results if "Bulk insert_many" in r.test_name), None)
        
        if single and bulk:
            comparison = metrics.compare_results(single, bulk)
            report.add_comparison("MongoDB: Single vs. Bulk Insert", comparison)
    
    elif test_name == "postgres":
        # Single Commits vs. Transactional vergleichen
        single = next((r for r in results if "Single Commits" in r.test_name), None)
        batch = next((r for r in results if "Transactional Batch" in r.test_name), None)
        
        if single and batch:
            comparison = metrics.compare_results(single, batch)
            report.add_comparison("PostgreSQL: Single Commits vs. Transactional", comparison)
    
    elif test_name == "vector":
        # KNN vs. ANN vergleichen
        knn = next((r for r in results if "KNN" in r.test_name), None)
        ann = next((r for r in results if "ANN (HNSW)" in r.test_name and "Filtered" not in r.test_name), None)
        
        if knn and ann:
            comparison = metrics.compare_results(knn, ann)
            report.add_comparison("pgvector: KNN (exakt) vs. ANN (HNSW)", comparison)


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
        selected_tests = ["redis", "mongo", "postgres", "vector"]
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
