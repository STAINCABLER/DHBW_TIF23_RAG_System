# Planung: Embedding-KI für unser RAG-System

Dieses Dokument beschreibt, wie unsere Embedding-KI im RAG-System eingesetzt wird – sowohl beim **Erstellen** (Ingestion) der Embeddings als auch beim **Auswerten** (Query). Es dient als technische Planungsgrundlage.

---

## Ziel der Embedding-KI

Die Embedding-KI hat genau eine Aufgabe: Texte in numerische Vektoren umzuwandeln.  
Diese Vektoren werden:

- beim Ingest für **Dokument-Chunks** berechnet und in PostgreSQL gespeichert  
- bei einer Anfrage für die **User-Frage** berechnet und für die Vektor-Suche genutzt  

Die Embedding-KI entscheidet **nicht** über die Antwort – sie liefert nur Vektoren, die das Backend in der Datenbank vergleicht.

---

## A. Aufgaben beim Erstellen (Ingestion)

### 1. API/Funktion definieren

Wir definieren eine einheitliche Schnittstelle für Embeddings:

- Funktion/Service: `embed(text: string) -> float[]`
- Optional: `embed_many(texts: string[]) -> float[][]` für Batches

Diese Funktion kann z.B. über einen kleinen HTTP-Service (`POST /embed`) oder direkt als Library-Funktion im Backend implementiert sein.

### 2. Chunks an die Embedding-KI übergeben

Beim Dokument-Upload/Ingest passiert:

1. Dokument wird in MongoDB gespeichert (`documents`-Collection).
2. Dokument wird in Chunks zerlegt (Chunking-Logik wie in unserer Chunking-Doku).
3. Für jeden neuen Chunk:
   - Der Chunk-Text wird an `embed(chunk_text)` übergeben.
   - Das Ergebnis ist ein Embedding-Vektor (float-Array).

Es werden nur neue oder geänderte Chunks eingebettet – keine doppelten Berechnungen für bereits vorhandene, unveränderte Chunks.

### 3. Embeddings in PostgreSQL speichern

Für jeden Chunk wird ein Datensatz in der Tabelle `chunk_embeddings` in PostgreSQL geschrieben:

- `chunk_id` – ID des Chunks (z.B. `_id` aus MongoDB)
- optional `source_document_id` – ID des zugehörigen Dokuments
- `embedding` – Vektor-Spalte (pgvector, z.B. `vector(1536)`)
- `created_at` – Zeitstempel der Erstellung

Damit existiert für jeden durchsuchbaren Chunk genau ein Embedding in PostgreSQL.

### 4. Konsistenz sicherstellen

- Es wird **immer dasselbe Embedding-Modell** verwendet (für Chunks und für Fragen).
- Die Dimension des Vektors (z.B. 768, 1024, 1536) muss zur Spaltendefinition `embedding vector(N)` in PostgreSQL passen.
- Modellwechsel bedeutet: Re-Embedding der betroffenen Chunks und ggf. Migration/Versionierung (`model_name`, `embedding_version`).

---

## B. Aufgaben beim Auswerten (Query)

### 5. Query-Embedding berechnen

Bei jeder User-Anfrage:

1. Die Rohfrage des Users (String) wird an `embed(user_question_text)` übergeben.
2. Die Embedding-KI liefert einen Query-Vektor zurück.
3. Dieser Query-Vektor wird **nicht** dauerhaft gespeichert, sondern nur für die aktuelle Suche verwendet (ephemeral).

### 6. Vektor-Suche in PostgreSQL

Das Backend führt mit dem Query-Embedding eine Vektor-Suche auf `chunk_embeddings` aus:

- SQL-Abfrage (Beispiel-Idee, Syntax abhängig von pgvector-Konfiguration):

  - Auswahl der Top‑k ähnlichsten Embeddings
  - Sortierung nach Ähnlichkeit (z.B. Cosine / L2 Distanz)

- Ergebnis: Liste der Top‑k Einträge mit mindestens:
  - `chunk_id`
  - optional Distanz / Score

Damit steht fest, welche Chunks semantisch am besten zur Frage passen.

### 7. Passende Chunks laden

- Mit den gefundenen `chunk_id`s liest das Backend die zugehörigen Chunks aus MongoDB (`chunks`-Collection).
- Optional können dazu die Metadaten aus der `documents`-Collection geladen werden (Titel, Quelle, Tags, etc.).
- Diese Chunks bilden den Kontext für die LLM-Antwort.

### 8. Kontext an das Antwort-LLM geben

Das Antwort-LLM (zweite KI im System) bekommt:

- die originale User-Frage
- die ausgewählten Chunks als Kontext

Der Prompt kann z.B. enthalten:

- Rolle/Instruktionen für das LLM (z.B. „antworte nur aus diesem Kontext“)
- Frage
- konkatenierten Text der relevanten Chunks

Das LLM erzeugt daraus die eigentliche Antwort für den User.

---

## C. Struktur der Embedding-KI als Service

### 9. Service-Design (minimal)

Minimalvariante eines Embedding-Services:

- HTTP-Endpoint `POST /embed`
  - Request-Body: `{ "text": "<string>" }`
  - Response-Body: `{ "embedding": [float, float, ...] }`
- Optionaler Batch-Endpoint `POST /embed_many`
  - Request-Body: `{ "texts": ["<string1>", "<string2>", ...] }`
  - Response-Body: `{ "embeddings": [[...], [...], ...] }`

Der Service kapselt die konkrete Einbindung des Embedding-Modells (z.B. OpenAI, Mistral, lokales Modell) und wird von Ingestion-Jobs und Query-Endpunkten aufgerufen.

### 10. Verwendung im Gesamtsystem

- **Ingestion-Job**
  - Ruft den Embedding-Service für alle neuen/änderten Chunks auf.
  - Schreibt die resultierenden Vektoren in `chunk_embeddings` in PostgreSQL.
- **Query-Endpunkt**
  - Ruft den Embedding-Service für die User-Frage auf.
  - Führt mit dem Query-Vektor eine Vektor-Suche auf `chunk_embeddings` aus.
  - Holt Chunks aus MongoDB und übergibt sie als Kontext an das Antwort-LLM.

---
