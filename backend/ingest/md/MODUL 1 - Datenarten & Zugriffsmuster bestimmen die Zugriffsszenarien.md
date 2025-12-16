# MODUL 1 — Datenarten & Zugriffsmuster bestimmen die Zugriffsszenarien

## 1. Ziel des Moduls

Nach diesem Modul kannst du:

- die wichtigsten Datenarten in modernen Systemen erkennen,
- typische Zugriffsmuster zuordnen,
- daraus konkrete Zugriffsszenarien ableiten,
- und verstehen, warum diese Szenarien die Grundlage jeder späteren Datenbankentscheidung sind.

**Wichtig:**
Dieses Modul ist noch keine DB-Auswahl.
Es ist die Grundlage dafür, welche Informationen du später noch sammeln musst, bevor du eine DB auswählen kannst.

## 2. Durchgehendes Beispiel (Customer-Service-RAG-System)

Wir nutzen im ganzen Modul ein einheitliches Szenario:

Ein Customer-Service-RAG-System unterstützt Support-Agents und nutzt:

- Kundendaten
- Produktdaten
- Chat-Verläufe
- interne Wissensartikel
- Chunks & Embeddings
- Sessions & Rate-Limits
- Logs & Monitoring

Alle Beispiele basieren auf diesen Objekten.

## 3. ACHSE 1: Datenarten (Was sind das für Daten?)

Datenarten beschreiben die Natur der Informationen.
Sie bestimmen, wie flexibel, wie groß, wie häufig änderbar und wie verknüpft Daten sind.

### 3.1 Strukturierte Daten (klassisch relational)

Eigenschaften:

- feste Felder
- klare Beziehungen (Joins)
- ACID-Anforderungen
- geringe Größe, häufig aktualisiert

Beispiele im RAG-System:

- Kundendaten (Adresse, Verträge)
- Produktkatalog

### 3.2 Semi-strukturierte Dokumente (JSON, Text, HTML)

Eigenschaften:

- flexible Struktur
- Abschnitte, Titel, Fließtext
- typisch für: Chunking, Volltextsuche
- können groß werden

Beispiele:

- Produktmanuals
- Wissensartikel
- lange Chat-Logs

### 3.3 Embeddings (Vektoren)

Eigenschaften:

- numerische Repräsentationen
- 256–4096 Dimensionen
- ausschließlich für ANN-Suche geeignet
- nicht sinnvoll „manuell“ zu durchsuchen

Beispiele:

- Embeddings von Chunks
- Embedding der Anfrage

### 3.4 Ephemerer Zustand (State)

Eigenschaften:

- sehr kurzlebig
- extrem schnelle Zugriffe
- oft überschrieben oder sofort gelöscht

Beispiele:

- Session-Kontext
- Rate-Limit-Zähler
- kurzfristiger Retrieval-Cache

### 3.5 Zeitreihen (Events, Logs, Monitoring)

Eigenschaften:

- viele kleine, kontinuierliche Writes
- strikt zeitlich sortiert
- selten aktualisiert, fast nie gelöscht
- Retention wichtig

Beispiele:

- LLM-Latenz-Logs
- Fehlermeldungen
- Monitoring-Daten

## 4. ACHSE 2: Zugriffsmuster (Wie werden Daten genutzt?)

Zugriffsmuster beschreiben Aktivitäten auf Daten.

### 4.1 Read-heavy

Sehr viele Reads, wenige oder keine Writes.
→ Beispiel: Chunks eines Manuals laden.

### 4.2 Write-heavy

Viele kontinuierliche Writes.
→ Beispiel: Monitoring-Events.

### 4.3 Read/Write Mixed (OLTP)

Regelmäßige Reads + Updates.
→ Beispiel: Kundendaten ändern.

### 4.4 Append-only

Nur hinzufügen, nie überschreiben.
→ Beispiel: Chat-Verlauf.

### 4.5 Bulk-Ingest

Große Mengen auf einmal einfügen.
→ Beispiel: neue Dokumente ingest.

### 4.6 Ultra-low-latency Key-Value

Zugriffe müssen in wenigen Millisekunden erfolgen.
→ Beispiel: Session-Daten, Rate-Limits.

## 5. Zugriffsszenarien: Die Kombination von Datenart × Zugriffsmuster

Ein Zugriffsszenario ist die präzise Beschreibung, wie ein bestimmtes Objekt im System genutzt wird.

Es besteht aus:

- Datenart
- Zugriffsmuster
- kurzformiger Nutzungserklärung

Beispiel:
„Dokument (Datenart) + read-heavy (Muster) → Chunk Retrieval (Szenario)“

Das Zugriffsszenario ist der erste Baustein für spätere Entscheidungen.

**Wichtig:**
Ein Zugriffsszenario bestimmt noch nicht die Datenbank.
Dafür fehlen noch Workload, Risiken, Latenzen — die kommen in Modul 2 & 3.

## 6. Beispiele aus dem Customer-Service-RAG

### 6.1 Chunks eines Dokuments

- Datenart: Dokument
- Zugriffsmuster: read-heavy
- Zugriffsszenario: „Chunk Retrieval für jede Agent-Anfrage"

### 6.2 Embeddings

- Datenart: Vektor
- Zugriffsmuster: ANN-Suche
- Zugriffsszenario: „Ähnlichkeitssuche für Top-K Retrieval"

### 6.3 Session-Kontext

- Datenart: State
- Zugriffsmuster: ultra-low-latency
- Zugriffsszenario: „Kontext pro Anfrage lesen und aktualisieren"

### 6.4 Chat-Historie

- Datenart: Dokument
- Zugriffsmuster: append-only
- Zugriffsszenario: „Nachricht an Verlauf anhängen"

### 6.5 Kundendaten

- Datenart: Strukturierte Daten
- Zugriffsmuster: read/write mixed
- Zugriffsszenario: „Profil-Lookup plus Änderung eines Feldes"

### 6.6 Logs & Monitoring

- Datenart: Zeitreihe
- Zugriffsmuster: write-heavy
- Zugriffsszenario: „Event Logging"

## 7. Profi-Hinweis (kurz & strategisch): Warum Datenart NICHT die DB bestimmt

Damit du nicht in Schema-F fällst:

Die Datenart bestimmt NICHT automatisch die Datenbank.

Warum?

Weil spätere Module zeigen, dass zusätzlich relevant sind:

- Konsistenzanforderungen
- kritische Operationen (kritischer Pfad)
- Lastspitzen & Workloads
- Latenzbudgets
- Team-Skills & Betreibbarkeit

Diese Aspekte kommen in:

- Modul 2: Zahlen & Workloads
- Modul 3: Risiko-Management & DB-Auswahl

Modul 1 bereitet dich darauf vor, welche Objekte überhaupt existieren und wie sie genutzt werden.

## 8. Capstone-Relevanz (Pflicht!)

In deiner schriftlichen Abgabe wird bewertet, ob du:

- ✔ alle Datenarten korrekt identifiziert hast
- ✔ zu jedem Objekt das passende Zugriffsmuster festgelegt hast
- ✔ für jedes Objekt ein klares Zugriffsszenario formuliert hast
- ✔ sauber trennst:
  - Dokument vs. Vektor
  - persistent vs. ephemeral
  - append-only vs. update
- ✔ später aus diesen Szenarien Workloads ableiten kannst

Ohne dieses Modul kannst du den Capstone nicht erfolgreich lösen.

## 9. Mini-Aufgabe (10–15 Minuten)

Ordne für jedes der folgenden Objekte zu:

- Datenart
- Zugriffsmuster
- Zugriffsszenario

Objekte:

- A) „Troubleshooting-Manual Kaffeemaschine"
- B) „Embedding von chunk_42"
- C) „Rate-Limit Counter user_123"
- D) „Kundenprofil (Adresse, Verträge)"
- E) „Chat-Verlauf einer Support-Session"

Die Musterlösung findest du im PDF „Lösungen Modul 1“.

## 10. Check: Habe ich Modul 1 verstanden?

Kannst du für ein beliebiges Objekt:

- die Datenart eindeutig bestimmen?
- das Zugriffsmuster korrekt zuordnen?
- daraus ein Zugriffsszenario formulieren?
- erklären, warum diese Einordnung für spätere Entscheidungen wichtig ist?

Wenn ja → Modul 1 abgeschlossen.
Weiter zu Modul 2: Workloads definieren.
