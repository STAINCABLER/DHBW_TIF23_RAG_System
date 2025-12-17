"""
Report Generator - Erstellung des Markdown Performance Reports
===============================================================

Dieses Modul generiert den finalen Markdown-Report mit allen
Testergebnissen, Vergleichen und Erkenntnissen.

Report-Struktur:
    1. Übersicht & Zusammenfassung
    2. Systemkonfiguration
    3. Ergebnisse pro Szenario (Tabellen)
    4. Vergleiche (Single vs. Batch, Sync vs. Async)
    5. SLO-Analyse (50ms Budget für Vektorsuche)
    6. Schlussfolgerungen

Modul-Referenz:
    - Anforderungen 1.3: Reporting
    - Anforderungen 5.6: Report-Ausgabe

Autor: RAG Performance Test Suite
"""

import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from .metrics import TestResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generiert den Markdown Performance Report.
    
    Diese Klasse sammelt alle Testergebnisse und erstellt einen
    übersichtlichen Report im Markdown-Format, der alle Metriken
    in Tabellenform darstellt.
    
    Beispiel:
        generator = ReportGenerator(config)
        
        # Ergebnisse hinzufügen
        generator.add_result(redis_result)
        generator.add_result(mongo_result)
        
        # Vergleich hinzufügen
        generator.add_comparison("Single vs. Batch", comparison_data)
        
        # Report generieren
        report_path = generator.generate()
    """
    
    def __init__(self, config: dict, base_path: Optional[Path] = None):
        """
        Initialisiert den Report Generator.
        
        Args:
            config: Die geladene Konfiguration aus test_config.yaml
            base_path: Basisverzeichnis für Report-Ausgabe
        """
        self.config = config
        self.base_path = base_path or Path(__file__).parent.parent
        
        # Reporting-Konfiguration
        report_config = config.get("reporting", {})
        self.output_dir = self.base_path / report_config.get("output_dir", "reports")
        self.filename_pattern = report_config.get(
            "filename_pattern", "report_{timestamp}.md"
        )
        self.timestamp_format = report_config.get(
            "timestamp_format", "%Y-%m-%d_%H-%M-%S"
        )
        self.include_system_info = report_config.get("include_system_info", True)
        
        # Ergebnisse sammeln
        self.results: list[TestResult] = []
        self.comparisons: list[dict] = []
        self.notes: list[str] = []
        
        # Testlaufzeiten
        self.test_durations: dict[str, float] = {}
        self.total_duration: float = 0.0
        
        # Zeitstempel für den Report
        self.timestamp = datetime.now()
    
    def add_result(self, result: TestResult) -> None:
        """
        Fügt ein Testergebnis zum Report hinzu.
        
        Args:
            result: Das TestResult-Objekt
        """
        self.results.append(result)
        logger.info(f"Ergebnis hinzugefügt: {result.test_name}")
    
    def add_comparison(self, title: str, comparison: dict) -> None:
        """
        Fügt einen Vergleich zum Report hinzu.
        
        Args:
            title: Titel des Vergleichs (z.B. "Redis: Single vs. Pipeline")
            comparison: Dictionary mit Vergleichsdaten
        """
        self.comparisons.append({"title": title, "data": comparison})
    
    def add_note(self, note: str) -> None:
        """
        Fügt eine Anmerkung zum Report hinzu.
        
        Args:
            note: Die Anmerkung
        """
        self.notes.append(note)
    
    def set_test_durations(self, test_durations: dict[str, float], total_duration: float) -> None:
        """
        Setzt die Testlaufzeiten für den Report.
        
        Args:
            test_durations: Dictionary mit Testname -> Laufzeit in Sekunden
            total_duration: Gesamtlaufzeit aller Tests in Sekunden
        """
        self.test_durations = test_durations
        self.total_duration = total_duration
        logger.info(f"Testlaufzeiten gesetzt: {len(test_durations)} Tests, Gesamt: {total_duration:.2f}s")
    
    def generate(self) -> Path:
        """
        Generiert den Markdown-Report.
        
        Returns:
            Pfad zur generierten Report-Datei
        """
        logger.info("Generiere Performance Report...")
        
        # Ausgabeverzeichnis erstellen
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Dateiname generieren
        timestamp_str = self.timestamp.strftime(self.timestamp_format)
        filename = self.filename_pattern.format(timestamp=timestamp_str)
        report_path = self.output_dir / filename
        
        # Report-Inhalt generieren
        content = self._generate_content()
        
        # Datei schreiben
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"✓ Report generiert: {report_path}")
        return report_path
    
    def _generate_content(self) -> str:
        """Generiert den vollständigen Report-Inhalt."""
        sections = [
            self._generate_header(),
            self._generate_summary(),
        ]
        
        if self.include_system_info:
            sections.append(self._generate_system_info())
        
        sections.extend([
            self._generate_results_section(),
            self._generate_comparisons_section(),
            self._generate_slo_analysis(),
            self._generate_test_durations_section(),
            self._generate_notes_section(),
            self._generate_footer(),
        ])
        
        return "\n\n".join(filter(None, sections))
    
    def _generate_header(self) -> str:
        """Generiert den Report-Header."""
        return f"""# RAG-System Datenbank Performance Report

**Generiert am:** {self.timestamp.strftime("%d.%m.%Y um %H:%M:%S")}

---

Dieser Report dokumentiert die Ergebnisse der Performance-Tests für das RAG-System.
Die Tests validieren die architektonischen Entscheidungen und prüfen die Einhaltung
der definierten SLOs (Service Level Objectives).

**Referenz:** Kursmaterialien Modul 2, 4, 7, 8"""
    
    def _generate_summary(self) -> str:
        """Generiert die Zusammenfassung mit vollständigem Ranking."""
        if not self.results:
            return "## Zusammenfassung\n\n*Keine Testergebnisse verfügbar.*"
        
        # Statistiken berechnen
        total_tests = len(self.results)
        total_operations = sum(r.total_operations for r in self.results)
        total_errors = sum(r.error_count for r in self.results)
        
        # Getestete Datenbanken
        databases_tested = sorted(set(r.database for r in self.results))
        
        # Kategorien ermitteln (SQL, NoSQL, Vector)
        categories_tested = sorted(set(getattr(r, 'category', 'Other') for r in self.results))
        
        # SLO-Status
        slo_results = [r for r in self.results if r.slo_met is not None]
        slo_passed = sum(1 for r in slo_results if r.slo_met)
        
        # Vollständiges Ranking nach Ops/s
        by_ops = sorted(self.results, key=lambda r: r.ops_per_second, reverse=True)
        
        # Dynamische Kategorien-Zuordnung erstellen
        category_to_dbs: dict[str, set[str]] = {}
        for r in self.results:
            cat = getattr(r, 'category', 'Other')
            if cat not in category_to_dbs:
                category_to_dbs[cat] = set()
            category_to_dbs[cat].add(r.database)
        
        # Kategorien-Tabelle dynamisch generieren
        category_rows = []
        for cat in sorted(category_to_dbs.keys()):
            dbs = sorted(category_to_dbs[cat])
            category_rows.append(f"| {cat} | {', '.join(dbs)} |")
        category_table = "\n".join(category_rows)
        
        summary = f"""## Zusammenfassung

| Metrik | Wert |
|--------|------|
| Anzahl Tests | {total_tests} |
| Getestete Datenbanken | {', '.join(databases_tested)} |
| Kategorien | {', '.join(categories_tested)} |
| Gesamtoperationen | {total_operations:,} |
| Fehler | {total_errors} |
| SLO-Tests | {slo_passed}/{len(slo_results)} bestanden |

### Datenbank-Kategorien (getestet)

| Kategorie | Datenbanken |
|-----------|-------------|
{category_table}

### Vollständiges Ranking (nach Ops/s)

| Rang | Test | Datenbank | Kategorie | Typ | Ops/s | P95 (ms) |
|------|------|-----------|-----------|-----|-------|----------|"""
        
        for i, r in enumerate(by_ops, 1):
            async_marker = "async" if r.is_async else "sync"
            category = getattr(r, 'category', 'Other')
            summary += f"\n| {i} | {r.test_name} | {r.database} | {category} | {async_marker} | {r.ops_per_second:,.0f} | {r.p95_latency_ms:.2f} |"
        
        return summary
    
    def _generate_system_info(self) -> str:
        """Generiert System-Informationen."""
        # Docker-Version abrufen
        try:
            docker_version = subprocess.run(
                ["docker", "--version"],
                capture_output=True, text=True, timeout=5
            ).stdout.strip()
        except Exception:
            docker_version = "Nicht verfügbar"
        
        return f"""## Systemkonfiguration

| Parameter | Wert |
|-----------|------|
| Betriebssystem | {platform.system()} {platform.release()} |
| Python-Version | {platform.python_version()} |
| Prozessor | {platform.processor() or 'N/A'} |
| Docker | {docker_version} |

**Hinweis:** Da die Tests lokal in Docker-Containern laufen, ist der
Netzwerk-Overhead minimal. In einer produktiven Umgebung können die
Latenzen höher sein."""
    
    def _generate_results_section(self) -> str:
        """Generiert den Ergebnisbereich, gruppiert nach Kategorie, Datenbank UND Operationstyp."""
        if not self.results:
            return ""
        
        # Nach Kategorie gruppieren
        by_category: dict[str, dict[str, list[TestResult]]] = {}
        for r in self.results:
            category = getattr(r, 'category', 'Other')
            if category not in by_category:
                by_category[category] = {}
            if r.database not in by_category[category]:
                by_category[category][r.database] = []
            by_category[category][r.database].append(r)
        
        sections = ["## Detaillierte Ergebnisse"]
        
        # Definiere Reihenfolge der Kategorien
        category_order = [
            "SQL", "NoSQL/Document", "NoSQL/Vector", "Vector Search",
            "E2E/Ingest", "E2E/Storage", "E2E/Vector Search", "Other"
        ]
        
        # Füge alle gefundenen Kategorien hinzu, die nicht in der Ordnung sind
        all_categories = set(by_category.keys())
        for cat in all_categories:
            if cat not in category_order:
                category_order.append(cat)
        
        for category in category_order:
            if category not in by_category:
                continue
                
            sections.append(f"\n### Kategorie: {category}")
            
            for db_name in sorted(by_category[category].keys()):
                results = by_category[category][db_name]
                sections.append(f"\n#### {db_name}")
                
                # Innerhalb der DB nach Operationstyp gruppieren
                by_op_type: dict[str, list[TestResult]] = {}
                for r in results:
                    op_type = r.operation_type or "other"
                    if op_type not in by_op_type:
                        by_op_type[op_type] = []
                    by_op_type[op_type].append(r)
                
                for op_type in ["write", "read", "vector_search", "parse", "chunk", "embed", "other"]:
                    if op_type not in by_op_type:
                        continue
                    op_results = by_op_type[op_type]
                    op_label = {
                        "write": "📝 Schreib-Operationen (Write)",
                        "read": "📖 Lese-Operationen (Read)",
                        "vector_search": "🔍 Vektorsuche",
                        "parse": "📄 Datei-Parsing",
                        "chunk": "✂️ Chunking",
                        "embed": "🧠 Embedding-Generierung",
                        "other": "📦 Sonstige"
                    }.get(op_type, op_type.capitalize())
                    
                    sections.append(f"\n##### {op_label}\n")
                    sections.append(self._generate_results_table(op_results))
        
        return "\n".join(sections)
    
    def _generate_results_table(self, results: list[TestResult]) -> str:
        """Generiert eine Ergebnistabelle."""
        table = """| Test | Operationen | Dauer (ms) | Ops/s | Mean (ms) | P95 (ms) | P99 (ms) |
|------|-------------|------------|-------|-----------|----------|----------|"""
        
        for r in results:
            async_marker = " (async)" if r.is_async else ""
            table += f"""
| {r.test_name}{async_marker} | {r.total_operations:,} | {r.total_duration_ms:,.1f} | {r.ops_per_second:,.0f} | {r.mean_latency_ms:.2f} | {r.p95_latency_ms:.2f} | {r.p99_latency_ms:.2f} |"""
        
        return table
    
    def _generate_comparisons_section(self) -> str:
        """Generiert den Vergleichsbereich, gruppiert nach Kategorie."""
        if not self.comparisons:
            return ""
        
        sections = ["## Vergleiche"]
        
        # Vergleiche nach Kategorie gruppieren
        comparison_groups = {
            "Intra-Datenbank (innerhalb einer DB)": [],
            "SQL-Datenbanken": [],
            "NoSQL-Datenbanken": [],
            "Cross-Category (SQL vs. NoSQL)": [],
            "Vector Search": [],
            "E2E (End-to-End)": [],
            "Sonstige": []
        }
        
        for comp in self.comparisons:
            title = comp["title"]
            
            # Kategorisierung basierend auf Titel
            if "Cross-Category" in title:
                comparison_groups["Cross-Category (SQL vs. NoSQL)"].append(comp)
            elif "SQL Batch" in title or "SQL Single" in title:
                comparison_groups["SQL-Datenbanken"].append(comp)
            elif "NoSQL Bulk" in title or "NoSQL Single" in title:
                comparison_groups["NoSQL-Datenbanken"].append(comp)
            elif "Vector" in title or "pgvector" in title:
                comparison_groups["Vector Search"].append(comp)
            elif "E2E" in title:
                comparison_groups["E2E (End-to-End)"].append(comp)
            elif any(db in title for db in ["Redis:", "MongoDB:", "PostgreSQL:", "MySQL:", "MariaDB:", "MSSQL:", "CouchDB:"]):
                comparison_groups["Intra-Datenbank (innerhalb einer DB)"].append(comp)
            else:
                comparison_groups["Sonstige"].append(comp)
        
        # Gruppen in definierter Reihenfolge ausgeben
        group_order = [
            "Intra-Datenbank (innerhalb einer DB)",
            "SQL-Datenbanken",
            "NoSQL-Datenbanken",
            "Cross-Category (SQL vs. NoSQL)",
            "Vector Search",
            "E2E (End-to-End)",
            "Sonstige"
        ]
        
        for group_name in group_order:
            comps = comparison_groups.get(group_name, [])
            if not comps:
                continue
            
            sections.append(f"\n### {group_name}\n")
            
            for comp in comps:
                title = comp["title"]
                data = comp["data"]
                
                speedup = data.get("speedup_factor")
                ops_improvement = data.get("ops_improvement")
                
                if speedup and speedup > 0:
                    # Bestimme die Richtung des Vergleichs
                    if speedup >= 1:
                        speed_text = f"{speedup:.1f}x schneller"
                    else:
                        speed_text = f"{1/speedup:.1f}x langsamer"
                    
                    if ops_improvement and ops_improvement >= 1:
                        ops_text = f"{ops_improvement:.1f}x mehr"
                    elif ops_improvement:
                        ops_text = f"{1/ops_improvement:.1f}x weniger"
                    else:
                        ops_text = "N/A"
                    
                    p95_imp = data.get('p95_improvement', 0)
                    p99_imp = data.get('p99_improvement', 0)
                    
                    if p95_imp and p95_imp >= 1:
                        p95_text = f"{p95_imp:.1f}x besser"
                    elif p95_imp:
                        p95_text = f"{1/p95_imp:.1f}x schlechter"
                    else:
                        p95_text = "N/A"
                    
                    if p99_imp and p99_imp >= 1:
                        p99_text = f"{p99_imp:.1f}x besser"
                    elif p99_imp:
                        p99_text = f"{1/p99_imp:.1f}x schlechter"
                    else:
                        p99_text = "N/A"
                    
                    sections.append(f"""#### {title}

| Metrik | Verbesserungsfaktor |
|--------|---------------------|
| Geschwindigkeit | {speed_text} |
| Ops/s | {ops_text} |
| P95 Latenz | {p95_text} |
| P99 Latenz | {p99_text} |

**Baseline:** {data.get('baseline', 'N/A')}  
**Optimiert:** {data.get('comparison', 'N/A')}
""")
                else:
                    sections.append(f"""#### {title}

*Vergleichsdaten nicht verfügbar.*
""")
        
        return "\n".join(sections)
    
    def _generate_slo_analysis(self) -> str:
        """Generiert die SLO-Analyse (besonders für Vektorsuche)."""
        slo_results = [r for r in self.results if r.slo_target_ms is not None]
        
        if not slo_results:
            return ""
        
        sections = ["""## SLO-Analyse (Service Level Objectives)

Die folgenden Tests wurden gegen definierte Latenz-Ziele geprüft.
Gemäß Modul 7 ist das kritische Budget für die Vektorsuche ≤50ms (P95).

| Test | Ziel (ms) | P95 (ms) | Status |
|------|-----------|----------|--------|"""]
        
        for r in slo_results:
            status = "✅ Bestanden" if r.slo_met else "❌ Nicht bestanden"
            sections.append(
                f"| {r.test_name} | {r.slo_target_ms:.0f} | {r.p95_latency_ms:.2f} | {status} |"
            )
        
        return "\n".join(sections)
    
    def _generate_test_durations_section(self) -> str:
        """Generiert die Sektion mit den Testlaufzeiten."""
        if not self.test_durations:
            return ""
        
        sections = ["""## Testlaufzeiten

Die folgende Tabelle zeigt die Laufzeit jedes einzelnen Tests.

| Test | Laufzeit |
|------|----------|"""]
        
        # Sortiere nach Laufzeit (längste zuerst)
        sorted_durations = sorted(
            self.test_durations.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for test_name, duration in sorted_durations:
            # Formatiere die Laufzeit sinnvoll
            if duration >= 60:
                minutes = int(duration // 60)
                seconds = duration % 60
                duration_str = f"{minutes}m {seconds:.1f}s"
            else:
                duration_str = f"{duration:.2f}s"
            
            sections.append(f"| {test_name} | {duration_str} |")
        
        # Gesamtlaufzeit
        if self.total_duration >= 60:
            total_minutes = int(self.total_duration // 60)
            total_seconds = self.total_duration % 60
            total_str = f"{total_minutes}m {total_seconds:.1f}s"
        else:
            total_str = f"{self.total_duration:.2f}s"
        
        sections.append(f"\n**Gesamtlaufzeit:** {total_str}")
        
        return "\n".join(sections)
    
    def _generate_notes_section(self) -> str:
        """Generiert den Anmerkungsbereich."""
        if not self.notes:
            return ""
        
        notes_text = "\n".join(f"- {note}" for note in self.notes)
        return f"""## Anmerkungen

{notes_text}"""
    
    def _generate_footer(self) -> str:
        """
        Generiert den Report-Footer mit datenbasierten Schlussfolgerungen.
        
        WICHTIG: Es werden NUR Erkenntnisse aus den tatsächlich durchgeführten
        Tests generiert. Keine Annahmen oder Internet-Weisheiten!
        """
        if not self.results:
            return """---

*Report generiert von RAG Performance Test Suite*"""
        
        conclusions = []
        
        # Analysiere tatsächliche Vergleichsdaten
        for comp in self.comparisons:
            data = comp["data"]
            speedup = data.get("speedup_factor")
            if speedup and speedup > 1:
                baseline = data.get("baseline", "Baseline")
                comparison = data.get("comparison", "Optimiert")
                conclusions.append(
                    f"**{comparison}** war **{speedup:.1f}x schneller** als {baseline} "
                    f"(gemessen: {data.get('ops_improvement', speedup):.1f}x mehr Ops/s)."
                )
        
        # SLO-Ergebnisse analysieren
        slo_results = [r for r in self.results if r.slo_target_ms is not None]
        if slo_results:
            passed = [r for r in slo_results if r.slo_met]
            failed = [r for r in slo_results if not r.slo_met]
            
            if passed:
                for r in passed:
                    conclusions.append(
                        f"**{r.test_name}** hat das SLO von {r.slo_target_ms:.0f}ms eingehalten "
                        f"(P95: {r.p95_latency_ms:.2f}ms)."
                    )
            
            if failed:
                for r in failed:
                    conclusions.append(
                        f"⚠️ **{r.test_name}** hat das SLO von {r.slo_target_ms:.0f}ms NICHT eingehalten "
                        f"(P95: {r.p95_latency_ms:.2f}ms)."
                    )
        
        # Async vs Sync Vergleich (nur wenn beide vorhanden)
        sync_results = [r for r in self.results if not r.is_async]
        async_results = [r for r in self.results if r.is_async]
        
        if sync_results and async_results:
            # Finde vergleichbare Tests
            for async_r in async_results:
                # Suche nach passendem Sync-Test (gleiche DB, ähnlicher Name)
                base_name = async_r.test_name.replace("Async ", "").replace(" Async", "")
                for sync_r in sync_results:
                    if sync_r.database == async_r.database and base_name in sync_r.test_name:
                        if async_r.ops_per_second > sync_r.ops_per_second:
                            factor = async_r.ops_per_second / sync_r.ops_per_second
                            conclusions.append(
                                f"**{async_r.test_name}** (async) erreichte {factor:.1f}x mehr Ops/s "
                                f"als die synchrone Variante."
                            )
                        elif sync_r.ops_per_second > async_r.ops_per_second:
                            factor = sync_r.ops_per_second / async_r.ops_per_second
                            conclusions.append(
                                f"**{sync_r.test_name}** (sync) war {factor:.1f}x schneller als "
                                f"die asynchrone Variante (Overhead durch async/await)."
                            )
                        break
        
        # Footer zusammenbauen
        if conclusions:
            conclusion_text = "\n".join(f"- {c}" for c in conclusions)
            return f"""---

## Gemessene Erkenntnisse

Die folgenden Aussagen basieren **ausschließlich auf den durchgeführten Tests**:

{conclusion_text}

---

*Report generiert von RAG Performance Test Suite*  
*Hinweis: Alle Schlussfolgerungen sind empirisch aus diesem Testlauf abgeleitet.*"""
        else:
            return """---

## Hinweis

Für diesen Testlauf wurden keine direkten Vergleiche (Baseline vs. Optimiert) durchgeführt.
Führen Sie mehrere Testszenarien aus, um aussagekräftige Erkenntnisse zu generieren.

---

*Report generiert von RAG Performance Test Suite*"""
