# RAG System – Datenbanknutzung im Projekt

## Projektübersicht

Wir bauen ein RAG-System (Retrieval-Augmented Generation), bei dem User Dokumente hochladen können und das System diese Dokumente nutzt, um User-Fragen intelligent zu beantworten.

**Datenbanken im System:**
- MongoDB (Dokumenten-DB)
- PostgreSQL (Relationale DB)
- Redis (Cache/Session-Store)

---

## 1. MongoDB – Dokumentenspeicher

### Wofür nutzen wir MongoDB?

MongoDB speichert die **Originaldokumente** und deren rohe Struktur.

### Was kommt rein?

- Hochgeladene Dateien (PDFs, Word, Text)
- Dokument-Metadaten (Titel, Upload-Datum, Dateiformat)
- Extrahierter Volltext aus den Dokumenten

### Warum MongoDB?

- **Flexibles Schema:** Jedes Dokument kann unterschiedliche Felder haben (z.B. PDF hat andere Metadaten als Word)
- **Speichert große Texte:** Ideal für variabel strukturierte Inhalte
- **Einfache Abfrage:** Dokumente können schnell per ID oder Metadaten gefunden werden

### Beispiel-Struktur

```json
{
  "_id": "doc_12345",
  "title": "Produkthandbuch_2024.pdf",
  "upload_date": "2024-11-20",
  "file_type": "PDF",
  "full_text": "Dies ist der extrahierte Volltext...",
  "metadata": {
    "author": "Max Mustermann",
    "pages": 45
  }
}
```

---

## 2. PostgreSQL – Kernlogik & Vektoren

### Wofür nutzen wir PostgreSQL?

PostgreSQL ist die **Haupt-Datenbank** für alle strukturierten, geschäftskritischen Daten und Embeddings.

### Was kommt rein?

**Tabelle 1: Users (Benutzerverwaltung)**
- User-ID, Name, Email, Passwort-Hash, Rolle

**Tabelle 2: Chunks (Textabschnitte)**
- Chunk-ID, Dokument-ID (Referenz zu MongoDB), Text-Chunk, Position im Dokument

**Tabelle 3: Embeddings (Vektoren für Suche)**
- Embedding-ID, Chunk-ID, Vektor (z.B. 768 Dimensionen), Erstellungsdatum

**Tabelle 4: Queries (User-Anfragen & Logging)**
- Query-ID, User-ID, Frage, Antwort, verwendete Chunks, Zeitstempel

### Warum PostgreSQL?

- **Starke Strukturen:** Klare Beziehungen zwischen Usern, Chunks und Embeddings über Foreign Keys
- **pgvector-Extension:** Speichert Vektor-Embeddings direkt in Postgres und ermöglicht schnelle Ähnlichkeitssuche
- **Ein System für alles:** Metadaten + Vektoren gemeinsam abfragbar ohne zweite Datenbank
- **ACID-Transaktionen:** Garantiert Datenkonsistenz bei gleichzeitigen Zugriffen

### Beispiel-Tabellen

```sql
-- User-Tabelle
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100) UNIQUE,
  password_hash VARCHAR(255),
  role VARCHAR(50)
);

-- Chunks-Tabelle
CREATE TABLE chunks (
  id SERIAL PRIMARY KEY,
  document_id VARCHAR(100),  -- Referenz zu MongoDB
  chunk_text TEXT,
  chunk_index INT
);

-- Embeddings mit pgvector
CREATE TABLE embeddings (
  id SERIAL PRIMARY KEY,
  chunk_id INT REFERENCES chunks(id),
  embedding vector(768),  -- 768-dimensionaler Vektor
  created_at TIMESTAMP
);

-- Query-Log
CREATE TABLE queries (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  question TEXT,
  answer TEXT,
  retrieved_chunks INT[],
  created_at TIMESTAMP
);
```

### Vektorsuche mit pgvector

```sql
-- Finde die 5 ähnlichsten Chunks zu einer User-Frage
SELECT c.chunk_text, 
       1 - (e.embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM embeddings e
JOIN chunks c ON e.chunk_id = c.id
ORDER BY e.embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

Der `<=>` Operator berechnet die Kosinus-Distanz zwischen Vektoren.

---

## 3. Redis – Schneller Zugriff & Sessions

### Wofür nutzen wir Redis?

Redis speichert **temporäre Daten** für sehr schnellen Zugriff.

### Was kommt rein?

- User-Sessions (wer ist eingeloggt?)
- Zwischengespeicherte Antworten (Cache häufiger Fragen)
- Rate-Limits (wie viele Anfragen pro User/Minute)

### Warum Redis?

- **Extrem schnell:** In-Memory-Datenbank, Antwortzeiten in Millisekunden
- **Einfache Key-Value-Struktur:** Perfekt für Sessions und Caches
- **Entlastet PostgreSQL:** Vermeidet unnötige DB-Anfragen

### Beispiel-Daten

```redis
# User-Session (60 Minuten gültig)
SET session:abc123 "user_id:42" EX 3600

# Cache für häufige Frage
SET cache:question:hash_xyz "Antwort auf häufige Frage..." EX 600

# Rate-Limit (max 10 Anfragen pro Minute)
INCR ratelimit:user:42:2024-11-24-14:00
EXPIRE ratelimit:user:42:2024-11-24-14:00 60
```

---

## 4. Zusammenspiel der Datenbanken im RAG-Flow

### Schritt 1: Dokument hochladen

1. User lädt PDF hoch
2. **MongoDB:** Speichert Original-PDF und Metadaten
3. System extrahiert Text und teilt in Chunks
4. **PostgreSQL:** Speichert Chunks in `chunks`-Tabelle
5. System berechnet Embeddings für jeden Chunk
6. **PostgreSQL:** Speichert Vektoren in `embeddings`-Tabelle

### Schritt 2: User stellt Frage

1. User fragt: "Wie installiere ich Produkt X?"
2. **Redis:** Prüft, ob Antwort im Cache liegt → Falls ja, sofort zurückgeben
3. Falls nicht: System berechnet Embedding der Frage
4. **PostgreSQL:** Führt Vektorsuche aus, findet ähnlichste Chunks
5. System baut Kontext aus gefundenen Chunks
6. LLM generiert Antwort basierend auf Kontext
7. **PostgreSQL:** Loggt Frage, Antwort und verwendete Chunks in `queries`
8. **Redis:** Cached die Antwort für zukünftige gleiche Fragen

### Schritt 3: User-Verwaltung

1. User loggt sich ein
2. **PostgreSQL:** Prüft Email/Passwort in `users`-Tabelle
3. **Redis:** Erstellt Session-Token, speichert für 60 Minuten
4. Bei jeder Anfrage prüft System Token in Redis (schnell!)

---

## 5. Warum diese Kombination?

| Datenbank | Stärke | Unser Use Case |
|-----------|--------|----------------|
| **MongoDB** | Flexible Dokumente | Verschiedene Upload-Formate |
| **PostgreSQL** | Relationen + Vektoren | Business-Logik + Embeddings |
| **Redis** | Schnelligkeit | Sessions + Cache |

Diese Aufteilung ist ein **Standard-Pattern** in modernen RAG-Systemen:
- MongoDB für unstrukturierte Quelldaten
- PostgreSQL als zentrale Datenbank mit pgvector für Embeddings
- Redis für Performance-Optimierung

---

## 6. Technologie-Stack

```yaml
Datenbanken:
  - MongoDB 7.0+
  - PostgreSQL 16+ mit pgvector-Extension
  - Redis 7.0+

Deployment:
  - Docker Compose (alle drei DBs als Container)
  - Netzwerk: rag-network (interne Kommunikation)
  
Sprachen/Frameworks:
  - Backend: Python/FastAPI oder Node.js
  - Embeddings: OpenAI API oder lokales Modell (z.B. sentence-transformers)
  - LLM: OpenAI GPT-4 oder lokales Llama-Modell
```

---

## 7. Docker Compose Beispiel

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: rag-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - mongodb_data:/data/db
    networks:
      - rag-network

  postgres:
    image: pgvector/pgvector:pg16
    container_name: rag-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: raguser
      POSTGRES_PASSWORD: ragpass
      POSTGRES_DB: ragdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - rag-network

  redis:
    image: redis:7.0-alpine
    container_name: rag-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - rag-network

volumes:
  mongodb_data:
  postgres_data:
  redis_data:

networks:
  rag-network:
    driver: bridge
```

---

## Quellen

- Fraunhofer IESE RAG Architecture
- AWS RAG Documentation
- MongoDB Vector Search Guide
- PostgreSQL pgvector Documentation
- ZenML Vector Database Comparison
- IBM RAG Pattern Guide
- Hugging Face RAG Tutorial
- Microsoft Azure RAG Best Practices