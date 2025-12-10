# Anforderungen an RAG-System Datenbank Performance Tests

Diese Dokumentation definiert die Anforderungen an die Performance-Tests für das RAG-System. Ziel ist es, architektonische Entscheidungen durch messbare Daten zu validieren und sicherzustellen, dass die gewählten Datenbanktechnologien den definierten Workloads (siehe Modul 2 & 4) standhalten.

Grundlage für diese Tests sind die Kursmaterialien, insbesondere die Erkenntnisse zu Workloads, Query Paths und den spezifischen Stärken/Schwächen von Redis, MongoDB und PostgreSQL.

## 1. Allgemeine Anforderungen

### 1.1 Technologie-Stack
*   **Sprache:** Alle Tests müssen in **Python** implementiert sein.
*   **Treiber:** Es sind die offiziellen oder performantesten Python-Treiber zu verwenden (z.B. `redis-py`, `pymongo`, `psycopg` oder `asyncpg`).
*   **Umgebung:** Die Datenbanken müssen als **Docker-Container** laufen.

### 1.2 Automatisierung & Lifecycle
*   Das Test-Skript muss in der Lage sein, die benötigte Infrastruktur selbstständig bereitzustellen.
*   **Setup:** Automatisches Starten der Docker-Container für Redis, MongoDB und PostgreSQL vor Testbeginn.
*   **Konfiguration:** Initiale Konfiguration der Datenbanken (z.B. Erstellen von Tabellen, Indizes, Extensions wie `pgvector`).
*   **Teardown:** Automatisches Stoppen und Entfernen der Container nach Abschluss der Tests (oder bei Abbruch), um Ressourcen freizugeben.

### 1.3 Reporting
*   Am Ende der Testausführung muss ein ausführlicher **Markdown-Report** generiert werden.
*   Der Report muss enthalten:
    *   Beschreibung des Testszenarios.
    *   Verwendete Parameter (Anzahl Operationen, Batch-Größen, etc.).
    *   Messergebnisse:
        *   Gesamtdauer.
        *   Operationen pro Sekunde (Ops/s).
        *   Durchschnittliche Latenz.
        *   **P95 und P99 Latenzen** (besonders wichtig für Critical Paths, siehe Modul 4).
    *   Vergleichswerte (z.B. "Single vs. Batch").

### 1.4 Code-Qualität & Dokumentation
*   Der Code muss ausführlich kommentiert sein.
*   Jedes Testszenario muss einen Kontext-Block (Docstring/Kommentar) haben, der erklärt:
    *   *Warum* testen wir das? (Bezug zu Modul/Theorie).
    *   *Was* ist die Erwartungshaltung? (Hypothese).

---

## 2. Zu testende Szenarien (Workloads)

Die Tests müssen verschiedene Workload-Dimensionen (Häufigkeit, Parallelität, Datenmenge) abdecken. Basierend auf den Kursmaterialien sind folgende Szenarien zwingend:

### Szenario A: Write Performance (Ingest & Updates)
*Ziel: Verifikation der Erkenntnisse aus "Performance-Myth-Busting" (Modul 8).*

1.  **Redis:**
    *   **Naive Writes:** 10.000 einzelne `SET` Operationen.
    *   **Pipelining:** 10.000 `SET` Operationen in einer Pipeline.
    *   *Kontext:* Test des Roundtrip-Overheads vs. Batch-Effizienz.

2.  **MongoDB:**
    *   **Single Inserts:** 10.000 Dokumente einzeln einfügen.
    *   **Bulk Inserts:** 10.000 Dokumente mittels `insert_many` einfügen.
    *   *Kontext:* Relevanz für den Ingest-Prozess von Chunks (Modul 6).

3.  **PostgreSQL:**
    *   **Single Commits:** 10.000 `INSERT`s mit jeweils eigenem Commit.
    *   **Transactional Batch:** 10.000 `INSERT`s in einer einzigen Transaktion.
    *   *Kontext:* Verständnis von WAL, fsync und Transaktionskosten (ACID).

### Szenario B: Read Performance (Critical Query Paths)
*Ziel: Simulation der Latenz im "RAG Answer" Pfad (Modul 4).*

1.  **Key-Value Lookup (Redis):**
    *   Abruf von Session-Daten oder Rate-Limit-Checks.
    *   Messung der Latenz bei hoher Frequenz.

2.  **Document Retrieval (MongoDB):**
    *   Abruf von Chunks anhand ihrer ID (nachdem die Vektorsuche IDs geliefert hat).
    *   Vergleich: Abruf einzelner Dokumente vs. `find({_id: {$in: [...]}})` für mehrere Chunks.

3.  **Structured Query (PostgreSQL):**
    *   Abruf von User-Profilen oder Metadaten mit Filtern (WHERE-Clause).
    *   Test mit und ohne Index.

### Szenario C: Vector Search (Der 50ms Engpass)
*Ziel: Validierung des "Vektor-DB-Zwangs" und Einhaltung des SLOs (Modul 7).*

1.  **Setup:**
    *   Generierung von Dummy-Vektoren (z.B. 768 Dimensionen, float32).
    *   Einfügen von 10.000 - 100.000 Vektoren in PostgreSQL (`pgvector`) und/oder MongoDB (Atlas Vector Search Simulation/Mock wenn lokal nicht verfügbar, sonst lokal).

2.  **Tests:**
    *   **Exact Search (KNN):** Lineare Suche (hohe Präzision, langsam).
    *   **Approximate Search (ANN):** Suche mit HNSW-Index.
    *   **Metadaten-Filterung:** Suche kombiniert mit einem Filter (z.B. `category='A'`).

3.  **Metriken:**
    *   Erreicht die Query das **< 50ms Budget** (P95)?
    *   Wie stark beeinflusst die Datenmenge die Suchzeit (Skalierbarkeit)?

---

## 3. Datenmodellierung für Tests

Um realistische Ergebnisse zu erhalten, sollten die Testdaten den Strukturen aus den Modulen entsprechen:

*   **Chunks (MongoDB):** JSON-Dokumente mit Textinhalt (~500-1000 Zeichen), Metadaten (Quelle, Seite) und Embedding-Referenz.
*   **Vektoren:** Arrays aus Floats, normalisiert.
*   **Relationale Daten (PostgreSQL):** Tabellen für User, Logs oder strukturierte Metadaten.

## 4. Implementierungshinweise

*   Nutze Bibliotheken wie `Faker` für Textdaten und `numpy` für Vektoren.
*   Verwende `time.perf_counter_ns()` für präzise Zeitmessungen.
*   Stelle sicher, dass Docker-Volumes bereinigt werden, um Seiteneffekte zwischen Testläufen zu vermeiden.
*   Fehlerbehandlung: Wenn ein Test fehlschlägt, muss der Report dies vermerken, aber die Aufräumarbeiten (Docker stop) müssen trotzdem erfolgen.


