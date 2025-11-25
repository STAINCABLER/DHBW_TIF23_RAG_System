# RAG-System – Sinnvolle Datenbankstrukturen

## 1. MongoDB (Dokumentenorientierte DB für Rohdaten)

### Zweck
- Speicherung der Originaldokumente und deren Metadaten in flexibler Dokumentenstruktur.

### Sammlung: `documents`
```json
{
  "_id": "doc_12345",
  "title": "Benutzerhandbuch_V1.pdf",
  "upload_date": "2025-11-24T13:45:00Z",
  "file_type": "pdf",
  "uploader": "user_01",
  "content_text": "Dies ist ein Beispieltext...",
  "metadata": {
    "author": "Max Mustermann",
    "pages": 14,
    "language": "de",
    "source": "upload"
  },
  "status": "parsed",
  "parsed_chunks": [
    { "chunk_id": "chunk_1", "start": 0, "end": 350 },
    { "chunk_id": "chunk_2", "start": 351, "end": 800 }
  ]
}
```
- **Hinweis:** Roh-Dateien (PDF, DOCX, Images) werden üblicherweise nicht direkt in MongoDB gespeichert, sondern im Filesystem/Blob Storage (z.B. S3, GridFS) und hier nur der Pfad als Referenz abgelegt.

### Indexierung
- Index auf: `upload_date`, `file_type`, `uploader`, `status`
- Fulltext-Index (z.B. Atlas Search) auf `content_text`

### Abfragen
- Finde alle PDFs eines Users:
  ```js
  db.documents.find({ uploader: "user_01", file_type: "pdf" })
  ```
- Suche im Volltext:
  ```js
  db.documents.find({ $text: { $search: "Installationsanweisung" } })
  ```

---

## 2. PostgreSQL (Strukturierte DB für Kernlogik & Chunks)

### Zweck
- Verwaltung von Usern, Beziehungen, Chunks, Embeddings und Logs.

### Relevante Tabellen
```sql
-- users: Benutzerverwaltung
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(80),
  email VARCHAR(120) UNIQUE,
  password_hash VARCHAR(255)
);

-- documents: Metadaten, Verknüpft mit MongoDB
CREATE TABLE documents (
  id VARCHAR(64) PRIMARY KEY,
  title VARCHAR(200),
  uploader_id INT REFERENCES users(id),
  upload_date TIMESTAMP,
  file_type VARCHAR(20)
);

-- chunks: Textabschnitte
CREATE TABLE chunks (
  id SERIAL PRIMARY KEY,
  document_id VARCHAR(64) REFERENCES documents(id),
  chunk_index INT,
  chunk_text TEXT
);

-- embeddings: Vektoren
CREATE TABLE embeddings (
  id SERIAL PRIMARY KEY,
  chunk_id INT REFERENCES chunks(id),
  embedding vector(768),
  created_at TIMESTAMP
);

-- queries: Logs von User-Abfragen
CREATE TABLE queries (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  question TEXT,
  answer TEXT,
  created_at TIMESTAMP
);
```

### Indexierung
- Indizes auf chunks.document_id, embeddings.chunk_id, queries.user_id
- pgvector-Index auf embeddings.embedding

---

## 3. Redis (Cache & Session-Store)

### Zweck
- Blitzschneller Zugriff auf Sessions, Response-Caches, Rate-Limits.

### Key-Konventionen und Beispiele
```redis
# User-Session (Key: session:{token})
SET session:abc123 "user_id:42" EX 3600

# Cache einer häufigen Antwort (Key: cache:question:{hash})
SET cache:question:abcde123 "Antwort..." EX 300

# Rate Limit (Key: ratelimit:user:{user_id}:{timestamp_minute})
INCR ratelimit:user:42:2025-11-24-13:45
EXPIRE ratelimit:user:42:2025-11-24-13:45 60
```

---

## 4. Zusammenspiel

- Rohdaten & Metadaten kommen in MongoDB
- Nach dem Parsen: Chunk-Infos, Dokument-IDs (aus MongoDB) und Embeddings werden als strukturierte Referenzen nach PostgreSQL übertragen
- Temporäre Daten und schnelle Statusabfragen laufen über Redis