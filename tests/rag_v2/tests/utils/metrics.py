"""
Metrics Calculator - Berechnung von Performance-Metriken
=========================================================

Dieses Modul berechnet alle relevanten Performance-Metriken
aus den gemessenen Latenzzeiten.

Metriken:
    - Gesamtdauer
    - Operationen pro Sekunde (Ops/s)
    - Durchschnittliche Latenz (Mean)
    - Median Latenz (P50)
    - P95 und P99 Latenzen (kritisch für SLOs!)
    - Minimum und Maximum

Modul-Referenz:
    - Anforderungen 1.3: Reporting
    - Modul 4: Query Paths und Latenzbudgets
    - Modul 7: Das 50ms SLO für Vektorsuche

Autor: RAG Performance Test Suite
"""

import statistics
from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """
    Datenklasse für die Ergebnisse eines einzelnen Tests.
    
    Enthält alle Metriken, die im Report angezeigt werden.
    """
    # Identifikation
    test_name: str
    database: str
    operation_type: str  # "write", "read", "vector_search"
    
    # Basis-Metriken
    total_operations: int
    total_duration_ms: float
    
    # Datenbank-Kategorie (SQL, NoSQL/Document, NoSQL/Vector, etc.)
    category: str = "Other"
    
    # Berechnete Metriken (werden automatisch gefüllt)
    ops_per_second: float = 0.0
    mean_latency_ms: float = 0.0
    median_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    std_dev_ms: float = 0.0
    
    # Rohdaten (optional, für detaillierte Analyse)
    latencies_ms: list[float] = field(default_factory=list)
    
    # Zusätzliche Informationen
    batch_size: Optional[int] = None
    is_async: bool = False
    concurrent_clients: int = 1
    error_count: int = 0
    notes: str = ""
    
    # SLO-Prüfung
    slo_target_ms: Optional[float] = None
    slo_met: Optional[bool] = None


class MetricsCalculator:
    """
    Berechnet Performance-Metriken aus Latenzmessungen.
    
    Diese Klasse ist das Herzstück der Analyse. Sie nimmt die
    Rohdaten (Liste von Latenzzeiten) und berechnet alle
    statistischen Metriken, die für die Bewertung relevant sind.
    
    Besonders wichtig sind P95 und P99:
    - P95: 95% der Anfragen sind schneller als dieser Wert
    - P99: 99% der Anfragen sind schneller als dieser Wert
    
    Diese Perzentile sind entscheidend für SLOs (Service Level Objectives),
    wie das 50ms Budget für Vektorsuche (siehe Modul 7).
    
    Beispiel:
        calculator = MetricsCalculator()
        
        # Latenzen in Millisekunden
        latencies = [1.2, 1.5, 1.3, 2.0, 1.8, 50.0, ...]
        
        result = calculator.calculate(
            test_name="Redis Single SET",
            database="Redis",
            operation_type="write",
            latencies_ms=latencies,
            total_operations=10000
        )
        
        print(f"P99 Latenz: {result.p99_latency_ms} ms")
    """
    
    def calculate(
        self,
        test_name: str,
        database: str,
        operation_type: str,
        latencies_ms: list[float],
        total_operations: int,
        total_duration_ms: Optional[float] = None,
        batch_size: Optional[int] = None,
        is_async: bool = False,
        concurrent_clients: int = 1,
        error_count: int = 0,
        slo_target_ms: Optional[float] = None,
        notes: str = "",
        category: str = "Other"
    ) -> TestResult:
        """
        Berechnet alle Metriken aus den Latenzmessungen.
        
        Args:
            test_name: Name des Tests (z.B. "Redis Pipeline SET")
            database: Datenbankname (z.B. "Redis", "MongoDB")
            operation_type: Art der Operation ("write", "read", "vector_search")
            latencies_ms: Liste aller gemessenen Latenzzeiten in Millisekunden
            total_operations: Gesamtzahl der durchgeführten Operationen
            total_duration_ms: Gesamtdauer (falls nicht aus Latenzen berechenbar)
            batch_size: Batch-Größe (falls zutreffend)
            is_async: War der Test asynchron?
            concurrent_clients: Anzahl paralleler Clients
            error_count: Anzahl aufgetretener Fehler
            slo_target_ms: SLO-Zielwert in ms (für P95-Prüfung)
            notes: Zusätzliche Anmerkungen
        
        Returns:
            TestResult mit allen berechneten Metriken
        """
        # Grundlegende Validierung
        if not latencies_ms:
            logger.warning(f"Keine Latenzwerte für Test '{test_name}'")
            return TestResult(
                test_name=test_name,
                database=database,
                operation_type=operation_type,
                total_operations=total_operations,
                total_duration_ms=total_duration_ms or 0,
                category=category,
                error_count=error_count,
                notes="Keine Messwerte verfügbar"
            )
        
        # Sortierte Latenzen für Perzentilberechnung
        sorted_latencies = sorted(latencies_ms)
        n = len(sorted_latencies)
        
        # Gesamtdauer berechnen (falls nicht angegeben)
        if total_duration_ms is None:
            total_duration_ms = sum(latencies_ms)
        
        # Operationen pro Sekunde
        if total_duration_ms > 0:
            ops_per_second = (total_operations / total_duration_ms) * 1000
        else:
            ops_per_second = 0.0
        
        # Statistische Metriken
        mean_latency = statistics.mean(latencies_ms)
        median_latency = statistics.median(latencies_ms)
        min_latency = min(latencies_ms)
        max_latency = max(latencies_ms)
        
        # Standardabweichung (nur bei mehr als 1 Wert)
        if n > 1:
            std_dev = statistics.stdev(latencies_ms)
        else:
            std_dev = 0.0
        
        # Perzentile berechnen
        p95_latency = self._percentile(sorted_latencies, 95)
        p99_latency = self._percentile(sorted_latencies, 99)
        
        # SLO-Prüfung (basierend auf P95)
        slo_met = None
        if slo_target_ms is not None:
            slo_met = p95_latency <= slo_target_ms
        
        return TestResult(
            test_name=test_name,
            database=database,
            operation_type=operation_type,
            total_operations=total_operations,
            total_duration_ms=total_duration_ms,
            category=category,
            ops_per_second=ops_per_second,
            mean_latency_ms=mean_latency,
            median_latency_ms=median_latency,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            std_dev_ms=std_dev,
            latencies_ms=latencies_ms,
            batch_size=batch_size,
            is_async=is_async,
            concurrent_clients=concurrent_clients,
            error_count=error_count,
            slo_target_ms=slo_target_ms,
            slo_met=slo_met,
            notes=notes
        )
    
    def _percentile(self, sorted_data: list[float], percentile: float) -> float:
        """
        Berechnet das angegebene Perzentil.
        
        Args:
            sorted_data: Sortierte Liste von Werten
            percentile: Perzentil (0-100)
        
        Returns:
            Wert am angegebenen Perzentil
        """
        n = len(sorted_data)
        if n == 0:
            return 0.0
        
        # Index berechnen (lineare Interpolation)
        k = (n - 1) * (percentile / 100)
        f = int(k)
        c = f + 1 if f + 1 < n else f
        
        # Interpolation
        if f == c:
            return sorted_data[f]
        
        d0 = sorted_data[f] * (c - k)
        d1 = sorted_data[c] * (k - f)
        
        return d0 + d1
    
    def calculate_from_latencies(
        self,
        test_name: str,
        database: str,
        category: str,
        operation_type: str,
        latencies_ns: list[int],
        batch_size: Optional[int] = None,
        is_async: bool = False,
        concurrent_clients: int = 1,
        error_count: int = 0,
        slo_target_ms: Optional[float] = None,
        notes: str = ""
    ) -> TestResult:
        """
        Berechnet Metriken aus Nanosekunden-Latenzwerten.
        
        Convenience-Methode, die Nanosekunden in Millisekunden konvertiert
        und dann calculate() aufruft.
        
        Args:
            test_name: Name des Tests
            database: Datenbankname
            category: Datenbank-Kategorie (SQL, NoSQL/Document, etc.)
            operation_type: Art der Operation
            latencies_ns: Liste der Latenzwerte in Nanosekunden
            ... weitere Parameter wie bei calculate()
        
        Returns:
            TestResult mit allen Metriken
        """
        # Konvertiere Nanosekunden zu Millisekunden
        latencies_ms = [ns_to_ms(ns) for ns in latencies_ns]
        
        return self.calculate(
            test_name=test_name,
            database=database,
            operation_type=operation_type,
            latencies_ms=latencies_ms,
            total_operations=len(latencies_ns),
            batch_size=batch_size,
            is_async=is_async,
            concurrent_clients=concurrent_clients,
            error_count=error_count,
            slo_target_ms=slo_target_ms,
            notes=notes,
            category=category
        )
    
    def calculate_from_total_time(
        self,
        test_name: str,
        database: str,
        category: str,
        operation_type: str,
        total_operations: int,
        total_time_ns: int,
        batch_size: Optional[int] = None,
        is_async: bool = False,
        concurrent_clients: int = 1,
        error_count: int = 0,
        slo_target_ms: Optional[float] = None,
        notes: str = ""
    ) -> TestResult:
        """
        Berechnet Metriken aus Gesamtzeit (für Batch-Operationen).
        
        Bei Batch-Operationen wie executemany() haben wir nur die Gesamtzeit,
        nicht einzelne Latenzwerte. Diese Methode berechnet daraus
        durchschnittliche Latenz.
        
        Args:
            test_name: Name des Tests
            database: Datenbankname
            category: Datenbank-Kategorie
            operation_type: Art der Operation
            total_operations: Anzahl der Operationen
            total_time_ns: Gesamtzeit in Nanosekunden
            ... weitere Parameter
        
        Returns:
            TestResult mit durchschnittlichen Metriken
        """
        total_time_ms = ns_to_ms(total_time_ns)
        
        # Durchschnittliche Latenz berechnen
        if total_operations > 0:
            avg_latency_ms = total_time_ms / total_operations
            ops_per_second = (total_operations / total_time_ms) * 1000
        else:
            avg_latency_ms = 0.0
            ops_per_second = 0.0
        
        return TestResult(
            test_name=test_name,
            database=database,
            operation_type=operation_type,
            total_operations=total_operations,
            total_duration_ms=total_time_ms,
            category=category,
            ops_per_second=ops_per_second,
            mean_latency_ms=avg_latency_ms,
            median_latency_ms=avg_latency_ms,
            min_latency_ms=avg_latency_ms,
            max_latency_ms=avg_latency_ms,
            p95_latency_ms=avg_latency_ms,
            p99_latency_ms=avg_latency_ms,
            std_dev_ms=0.0,
            batch_size=batch_size,
            is_async=is_async,
            concurrent_clients=concurrent_clients,
            error_count=error_count,
            slo_target_ms=slo_target_ms,
            slo_met=avg_latency_ms <= slo_target_ms if slo_target_ms else None,
            notes=notes + " (Nur Gesamtzeit verfügbar)"
        )
    
    def compare_results(
        self, 
        baseline: TestResult, 
        comparison: TestResult
    ) -> dict:
        """
        Vergleicht zwei Testergebnisse.
        
        Nützlich für Vergleiche wie "Single vs. Batch" oder
        "Sync vs. Async".
        
        Args:
            baseline: Das Basisergebnis (z.B. naive Implementierung)
            comparison: Das Vergleichsergebnis (z.B. optimierte Version)
        
        Returns:
            Dictionary mit Verbesserungsfaktoren
        """
        def safe_ratio(a: float, b: float) -> Optional[float]:
            """Berechnet Verhältnis, verhindert Division durch Null."""
            if b == 0:
                return None
            return a / b
        
        return {
            "baseline": baseline.test_name,
            "comparison": comparison.test_name,
            "speedup_factor": safe_ratio(
                baseline.total_duration_ms, 
                comparison.total_duration_ms
            ),
            "ops_improvement": safe_ratio(
                comparison.ops_per_second, 
                baseline.ops_per_second
            ),
            "p95_improvement": safe_ratio(
                baseline.p95_latency_ms, 
                comparison.p95_latency_ms
            ),
            "p99_improvement": safe_ratio(
                baseline.p99_latency_ms, 
                comparison.p99_latency_ms
            ),
        }


def ns_to_ms(nanoseconds: int) -> float:
    """
    Konvertiert Nanosekunden zu Millisekunden.
    
    Hilfsfunktion für time.perf_counter_ns() Messungen.
    
    Args:
        nanoseconds: Zeit in Nanosekunden
    
    Returns:
        Zeit in Millisekunden
    """
    return nanoseconds / 1_000_000


def s_to_ms(seconds: float) -> float:
    """
    Konvertiert Sekunden zu Millisekunden.
    
    Hilfsfunktion für time.perf_counter() Messungen.
    
    Args:
        seconds: Zeit in Sekunden
    
    Returns:
        Zeit in Millisekunden
    """
    return seconds * 1000
