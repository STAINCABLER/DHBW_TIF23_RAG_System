# PostgreSQL Vektorembeddings für das RAG-System

Dieses Dokument beschreibt, wie wir in unserem RAG-System Embeddings in PostgreSQL speichern und für die semantische Suche (Vektor-Retrieval) verwenden. Es ergänzt unsere bestehende PostgreSQL-, MongoDB- und Redis-Dokumentation um die Vektor-Komponente (pgvector).  

## Ziel und Einordnung

Unser RAG-System nutzt bereits:
- MongoDB für Dokumente und Chunks
- PostgreSQL für Nutzer, Rollen, Berechtigungen und relationale Kerndaten
- Redis für Caching, Sessions und flüchtige Daten

Um echte semantische Suche zu ermöglichen, ergänzen wir PostgreSQL um eine Vektor-Tabelle, die Embeddings für unsere Dokument-Chunks speichert. Diese Vektoren werden bei jeder RAG-Anfrage zur Ähnlichkeitssuche verwendet.

## Erweiterung: pgvector und Embedding-Tabelle

### pgvector-Erweiterung

Für die Speicherung der Embeddings verwenden wir die PostgreSQL-Erweiterung **pgvector**, die einen eigenen Datentyp `vector` bereitstellt und Ähnlichkeitssuchen direkt in SQL ermöglicht.

- Vektortyp: `vector(DIMENSION)` (z. B. `vector(1536)` je nach Embedding-Modell)
- Vergleichsoperatoren: z. B. Cosine Distance oder L2-Distanz über spezielle Operatoren/Indexes

### Tabelle `chunk_embeddings`

Wir legen eine eigene Tabelle an, die Embeddings von Chunks speichert und diese mit den eigentlichen Chunks verknüpft:

- **Name:** `chunk_embeddings`
- **Zweck:** Speichert pro Dokument-Chunk genau ein Embedding-Vektor
- **Beziehung:** `chunk_id` verweist auf den zugehörigen Chunk (z. B. in MongoDB oder PostgreSQL)

**Schema (fachlich):**

- `id`: Primärschlüssel (UUID oder BIGSERIAL)
- `chunk_id`: Referenz auf den Chunk (z. B. String/UUID, der den Chunk in MongoDB identifiziert)
- `source_document_id`: optionale Referenz auf das Quelldokument
- `embedding`: Vektor-Spalte (`vector(N)`, z. B. `vector(1536)`)
- `created_at`: Zeitstempel der Erstellung
- optional: `model_name`, `embedding_version` für spätere Migrationen/Neuberechnungen

**Einordnung nach Capstone-Kriterien:**

- Datenart: **Vektor**
- Persistenz: **persistent**
- Schreibmuster: überwiegend **append-only**
  - Neue Embeddings beim erstmaligen Ingest eines Dokuments/Chunks
  - Optionale Updates bei Re-Embedding (z. B. Modellwechsel)
- Zugriffsmuster:
  - **Write:** Beim Ingest von Dokumenten werden für jeden Chunk einmalig Embeddings geschrieben
  - **Read:** Bei jeder RAG-Anfrage werden mehrere Embeddings (Top‑k) gelesen, um ähnliche Chunks zu finden

## Zusammenspiel mit MongoDB (Dokumente & Chunks)

Unsere Dokumente und Chunks liegen in MongoDB. Dort existieren u. a.:

- `documents`-Collection: Metadaten und ursprüngliche Inhalte
- `chunks`-Collection: Text-Chunks eines Dokuments mit Referenz auf `document_id`

Die Verknüpfung zwischen MongoDB und PostgreSQL erfolgt über IDs:

- In `chunk_embeddings.chunk_id` speichern wir die ID des Chunks (z. B. die `_id` aus MongoDB als String/UUID).
- Optional kann `source_document_id` eine zweite Referenz auf das ursprüngliche Dokument enthalten.

Dadurch bleiben Inhalt und Metadaten in MongoDB, während PostgreSQL den Vektor‑Index und die semantische Suche übernimmt.

## Ingestion-Flow mit Embeddings

Der bestehende Ingestion-Prozess (Dokument hochladen → in Chunks zerlegen → in MongoDB speichern) wird um einen Embedding-Schritt in PostgreSQL erweitert.

**Ablauf (vereinfacht):**

1. User/Admin lädt ein Dokument hoch.
2. Das Dokument wird in MongoDB als `document` gespeichert.
3. Der Inhalt wird in mehrere `chunks` aufgeteilt (Chunking-Strategie).
4. Für jeden `chunk`:
   - Der Chunk-Text wird an ein Embedding-Modell gesendet.
   - Das zurückgegebene Embedding wird in PostgreSQL in `chunk_embeddings` gespeichert:
     - `chunk_id` = ID des Chunks in MongoDB
     - `source_document_id` = ID des Dokuments
     - `embedding` = Vektor
     - `created_at` = aktueller Zeitstempel

**Zugriffsszenario (Ingestion):**

- Pro neuem Dokument entstehen *N* Chunks.
- Für jeden dieser *N* Chunks wird genau ein Insert in `chunk_embeddings` durchgeführt.
- Schreiblast konzentriert sich auf Upload-/Ingestion-Phasen.

## Query-Flow mit Vektor-Retrieval

Bei einer Benutzeranfrage wird die Vektor-Tabelle genutzt, um passende Chunks semantisch zu finden.

**Ablauf (vereinfacht):**

1. User stellt eine Frage in der Anwendung.
2. Das Backend erzeugt für diese Frage ein Query-Embedding (gleiches Modell wie für die Chunks).
3. Das Query-Embedding wird in einer SQL-Abfrage gegen `chunk_embeddings` verwendet:
   - Ähnlichkeitssuche (z. B. Cosine Distance) auf der Spalte `embedding`
   - Auswahl der Top‑k ähnlichsten Einträge
4. Für die gefundenen `chunk_id`s werden die zugehörigen Chunks und Dokumente aus MongoDB geladen.
5. Das Backend baut einen Prompt-Kontext aus den relevantesten Chunks.
6. Frage + Kontext werden an das LLM gesendet, das daraufhin eine Antwort erzeugt.

**Zugriffsszenario (Query):**

- Pro RAG-Request:
  - 1 Embedding-Berechnung für die User-Frage
  - 1 Vektor-Abfrage auf `chunk_embeddings` (Top‑k, z. B. 5–20 Treffer)
  - Mehrere Lesezugriffe auf MongoDB für die eigentlichen Chunk-Texte

`chunk_embeddings` ist damit klar **read-heavy** im Live-Betrieb: viele Leseabfragen, relativ wenige Schreibereignisse.

## Zusammenspiel mit bestehenden PostgreSQL-Tabellen

PostgreSQL speichert bereits:
- Nutzer, Rollen, Berechtigungen
- ggf. Audit-Logs, Feedback, weitere relationale Daten

Die Vektor-Tabelle `chunk_embeddings` ergänzt diese Struktur um eine reine Such-/Index-Komponente:

- Nutzer- und Berechtigungstabellen steuern, **wer** welche Daten abfragen darf.
- `chunk_embeddings` steuert, **welche Chunks** für eine Frage semantisch relevant sind.
- Audit-/Log-Tabellen können RAG-Requests und genutzte Chunk-IDs protokollieren (z. B. für Debugging oder Nachvollziehbarkeit).

Dadurch entsteht eine klare Trennung:
- **MongoDB:** Inhalte und Dokument-Chunks
- **PostgreSQL (klassisch):** Nutzer, Rechte, Logs, Geschäftsobjekte
- **PostgreSQL (pgvector):** Embeddings und semantische Suche
