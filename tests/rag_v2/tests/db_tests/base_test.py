"""
Base Performance Test - Abstrakte Basisklasse für alle Tests
=============================================================

Diese Klasse definiert die gemeinsame Struktur und Logik für alle
datenbankspezifischen Performance-Tests.

Jeder Test erbt von dieser Klasse und implementiert:
    - setup(): Verbindung herstellen, Daten vorbereiten
    - teardown(): Verbindung schließen, aufräumen
    - Spezifische Test-Methoden (write, read, etc.)

Modul-Referenz:
    - Anforderungen 1.4: Code-Qualität & Dokumentation
    - Anforderungen 2: Zu testende Szenarien

Autor: RAG Performance Test Suite
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from contextlib import contextmanager

from utils.metrics import MetricsCalculator, TestResult, ns_to_ms
from utils.data_generator import DataGenerator

logger = logging.getLogger(__name__)


@dataclass
class TestContext:
    """
    Kontext-Informationen für einen Test.
    
    Enthält die Konfiguration und gemeinsame Ressourcen,
    die für alle Tests verfügbar sein müssen.
    """
    config: dict
    data_generator: DataGenerator
    metrics_calculator: MetricsCalculator
    
    # Optionale Test-spezifische Daten
    test_data: dict = field(default_factory=dict)


class BasePerformanceTest(ABC):
    """
    Abstrakte Basisklasse für alle Performance-Tests.
    
    Diese Klasse implementiert das Template-Method-Pattern:
    - Die Grundstruktur (setup, run, teardown) ist vorgegeben
    - Konkrete Tests überschreiben spezifische Methoden
    
    Jeder Test muss einen Kontext-Block haben, der erklärt:
    - WARUM testen wir das? (Bezug zur Theorie/Modul)
    - WAS ist die Erwartungshaltung? (Hypothese)
    
    Beispiel für eine konkrete Implementierung:
    
        class RedisPerformanceTest(BasePerformanceTest):
            '''
            Redis Performance Tests
            
            WARUM: Redis ist der primäre Cache und Session-Store im RAG-System.
                   Wir testen die Performance für Rate-Limiting und Session-Daten.
                   (Referenz: Modul 4 - Query Paths)
            
            HYPOTHESE: 
                - Pipeline-Operationen sind 10-20x schneller als Einzeloperationen
                - P99 Latenz sollte unter 5ms liegen
            '''
            
            def setup(self):
                self.client = redis.Redis(...)
    """
    
    # =========================================================================
    # Klassen-Attribute (von Unterklassen zu überschreiben)
    # =========================================================================
    
    # Name der Datenbank (für Reports)
    DATABASE_NAME: str = "Unknown"
    
    # Beschreibung des Tests (WARUM und WAS)
    TEST_DESCRIPTION: str = "Keine Beschreibung verfügbar"
    
    def __init__(self, context: TestContext):
        """
        Initialisiert den Test.
        
        Args:
            context: TestContext mit Konfiguration und Ressourcen
        """
        self.context = context
        self.config = context.config
        self.data_generator = context.data_generator
        self.metrics = context.metrics_calculator
        
        # Ergebnisse sammeln
        self.results: list[TestResult] = []
        
        # Allgemeine Konfiguration extrahieren
        general = self.config.get("general", {})
        self.num_operations = general.get("num_operations", 10000)
        self.batch_size = general.get("batch_size", 1000)
        self.warmup_operations = general.get("warmup_operations", 100)
        self.concurrent_clients = general.get("concurrent_clients", 10)
        
        # Status
        self._is_setup = False
    
    # =========================================================================
    # Template Methods (Grundstruktur)
    # =========================================================================
    
    def run_all_tests(self) -> list[TestResult]:
        """
        Führt alle Tests dieser Klasse aus.
        
        Diese Methode orchestriert den gesamten Testlauf:
        1. Setup (Verbindung, Daten vorbereiten)
        2. Warmup (Connection-Pool stabilisieren)
        3. Alle definierten Tests ausführen
        4. Teardown (aufräumen)
        
        Returns:
            Liste aller TestResult-Objekte
        """
        logger.info("=" * 60)
        logger.info(f"Starte Tests für: {self.DATABASE_NAME}")
        logger.info("=" * 60)
        logger.info(f"Beschreibung:\n{self.TEST_DESCRIPTION}")
        logger.info("-" * 60)
        
        try:
            # Setup
            logger.info("Setup...")
            self.setup()
            self._is_setup = True
            
            # Warmup
            logger.info(f"Warmup ({self.warmup_operations} Operationen)...")
            self.warmup()
            
            # Tests ausführen
            logger.info("Führe Tests aus...")
            self._run_tests()
            
            logger.info(f"✓ {len(self.results)} Tests abgeschlossen")
            
        except Exception as e:
            logger.error(f"Fehler in {self.DATABASE_NAME} Tests: {e}")
            raise
        
        finally:
            # Teardown (immer ausführen!)
            if self._is_setup:
                logger.info("Teardown...")
                self.teardown()
        
        return self.results
    
    @abstractmethod
    def setup(self) -> None:
        """
        Bereitet den Test vor.
        
        Zu implementieren:
            - Datenbankverbindung herstellen
            - Tabellen/Collections erstellen
            - Testdaten vorbereiten
        """
        pass
    
    @abstractmethod
    def teardown(self) -> None:
        """
        Räumt nach dem Test auf.
        
        Zu implementieren:
            - Testdaten löschen
            - Verbindung schließen
        """
        pass
    
    def warmup(self) -> None:
        """
        Führt Warmup-Operationen durch.
        
        Standardimplementierung: Macht nichts.
        Kann von Unterklassen überschrieben werden.
        """
        pass
    
    @abstractmethod
    def _run_tests(self) -> None:
        """
        Führt die eigentlichen Tests aus.
        
        Zu implementieren:
            - Alle spezifischen Test-Methoden aufrufen
            - Ergebnisse zu self.results hinzufügen
        """
        pass
    
    # =========================================================================
    # Hilfsmethoden für Zeitmessung
    # =========================================================================
    
    @contextmanager
    def measure_time(self):
        """
        Context Manager für Zeitmessung.
        
        Beispiel:
            with self.measure_time() as timer:
                # Code, der gemessen werden soll
                ...
            
            duration_ms = timer.duration_ms
        """
        timer = Timer()
        timer.start()
        try:
            yield timer
        finally:
            timer.stop()
    
    def measure_latencies(
        self,
        operation: Callable,
        count: int,
        *args,
        **kwargs
    ) -> list[float]:
        """
        Misst die Latenz für wiederholte Operationen.
        
        Args:
            operation: Die auszuführende Funktion
            count: Anzahl der Wiederholungen
            *args, **kwargs: Argumente für die Operation
        
        Returns:
            Liste von Latenzzeiten in Millisekunden
        """
        latencies = []
        
        for i in range(count):
            start = time.perf_counter_ns()
            operation(*args, **kwargs)
            end = time.perf_counter_ns()
            
            latencies.append(ns_to_ms(end - start))
        
        return latencies
    
    def record_result(
        self,
        test_name: str,
        operation_type: str,
        latencies_ms: list[float],
        total_operations: int,
        total_duration_ms: Optional[float] = None,
        batch_size: Optional[int] = None,
        is_async: bool = False,
        concurrent_clients: int = 1,
        error_count: int = 0,
        slo_target_ms: Optional[float] = None,
        notes: str = ""
    ) -> TestResult:
        """
        Zeichnet ein Testergebnis auf.
        
        Convenience-Methode, die MetricsCalculator.calculate() aufruft
        und das Ergebnis zur Liste hinzufügt.
        
        Args:
            test_name: Name des Tests
            operation_type: "write", "read", oder "vector_search"
            latencies_ms: Gemessene Latenzzeiten
            total_operations: Gesamtzahl der Operationen
            ... (weitere Parameter siehe MetricsCalculator.calculate)
        
        Returns:
            Das erstellte TestResult
        """
        result = self.metrics.calculate(
            test_name=test_name,
            database=self.DATABASE_NAME,
            operation_type=operation_type,
            latencies_ms=latencies_ms,
            total_operations=total_operations,
            total_duration_ms=total_duration_ms,
            batch_size=batch_size,
            is_async=is_async,
            concurrent_clients=concurrent_clients,
            error_count=error_count,
            slo_target_ms=slo_target_ms,
            notes=notes
        )
        
        self.results.append(result)
        
        # Kurze Zusammenfassung loggen
        logger.info(
            f"  → {test_name}: {result.ops_per_second:,.0f} ops/s, "
            f"P95={result.p95_latency_ms:.2f}ms"
        )
        
        return result


class Timer:
    """
    Einfache Timer-Klasse für Zeitmessungen.
    
    Verwendet time.perf_counter_ns() für höchste Präzision.
    """
    
    def __init__(self):
        self._start: Optional[int] = None
        self._end: Optional[int] = None
    
    def start(self) -> None:
        """Startet den Timer."""
        self._start = time.perf_counter_ns()
        self._end = None
    
    def stop(self) -> None:
        """Stoppt den Timer."""
        self._end = time.perf_counter_ns()
    
    @property
    def duration_ns(self) -> int:
        """Gibt die Dauer in Nanosekunden zurück."""
        if self._start is None:
            return 0
        end = self._end if self._end is not None else time.perf_counter_ns()
        return end - self._start
    
    @property
    def duration_ms(self) -> float:
        """Gibt die Dauer in Millisekunden zurück."""
        return ns_to_ms(self.duration_ns)
    
    @property
    def duration_s(self) -> float:
        """Gibt die Dauer in Sekunden zurück."""
        return self.duration_ns / 1_000_000_000
