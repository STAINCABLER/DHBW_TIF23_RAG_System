# MongoDB - Dokumentenorientierte Datenbank

## Zweck im RAG-System

MongoDB speichert alle **unstrukturierten bis semi-strukturierten Inhalte**, die für die Beratungsempfehlungen relevant sind.

## Datenbankstruktur

### Collections

#### 1. `consulting_articles`
Enthält Beratungsinhalte zu verschiedenen Datenbanktypen.

```json
{
  "_id": ObjectId,
  "title": "String",
  "category": "relational|document|time-series|vector",
  "content": "String",
  "tags": ["tag1", "tag2"],
  "created_at": ISODate,
  "updated_at": ISODate,
  "embedding": [Float],
  "relevance_score": Number
}
```

#### 2. `database_features`
Eigenschaften und Features von Datenbanktypen.

```json
{
  "_id": ObjectId,
  "database_type": "PostgreSQL|MongoDB|Redis|TimescaleDB",
  "feature": "String",
  "description": "String",
  "pros": ["pro1", "pro2"],
  "cons": ["con1", "con2"],
  "use_cases": ["case1", "case2"],
  "performance_metrics": {
    "throughput": "Number",
    "latency": "Number",
    "scalability": "String"
  }
}
```

#### 3. `case_studies`
Fallstudien und reale Anwendungsbeispiele.

```json
{
  "_id": ObjectId,
  "title": "String",
  "description": "String",
  "problem_statement": "String",
  "chosen_database": "String",
  "alternatives_considered": ["db1", "db2"],
  "rationale": "String",
  "results": {
    "performance_improvement": "Percentage",
    "cost_reduction": "Percentage",
    "implementation_time": "Duration"
  },
  "lessons_learned": ["lesson1", "lesson2"]
}
```

#### 4. `comparison_matrices`
Vergleichstabellen zwischen Datenbanksystemen.

```json
{
  "_id": ObjectId,
  "name": "String",
  "databases_compared": ["db1", "db2", "db3"],
  "criteria": {
    "scalability": { "db1": 9, "db2": 7, "db3": 8 },
    "consistency": { "db1": 10, "db2": 5, "db3": 8 },
    "ease_of_use": { "db1": 7, "db2": 9, "db3": 6 },
    "cost": { "db1": 5, "db2": 8, "db3": 9 }
  },
  "summary": "String"
}
```

#### 5. `recommendations_cache`
Zwischengespeicherte Empfehlungen basierend auf Benutzerparametern.

```json
{
  "_id": ObjectId,
  "user_query_hash": "String",
  "requirements": {
    "scale": "small|medium|large",
    "query_pattern": "oltp|olap|mixed",
    "consistency_requirement": "strong|eventual",
    "latency_requirement": "low|medium|high"
  },
  "recommended_databases": [
    {
      "name": "String",
      "match_score": Number,
      "reasoning": "String"
    }
  ],
  "created_at": ISODate,
  "expires_at": ISODate
}
```

## Indexing-Strategie

```javascript
// Volltextsuche für Artikel
db.consulting_articles.createIndex({ content: "text", title: "text" });

// Kategorien schnell filtern
db.consulting_articles.createIndex({ category: 1 });

// Vector-Suche für Embeddings
db.consulting_articles.createIndex({ embedding: "2d" });

// Vergleich von Datenbanken
db.comparison_matrices.createIndex({ databases_compared: 1 });

// Datum-basierte Abfragen
db.case_studies.createIndex({ created_at: -1 });
```

## Abfrage-Beispiele

### Semantische Suche
```javascript
db.consulting_articles.find({
  embedding: {
    $near: {
      $geometry: { type: "Point", coordinates: [userEmbedding] }
    }
  }
}).limit(5);
```

### Kategoriebasierte Filterung
```javascript
db.consulting_articles.find({
  category: "relational",
  tags: { $in: ["scalability", "transactions"] }
});
```

### Case Studies für spezifische Datenbank
```javascript
db.case_studies.find({
  chosen_database: "PostgreSQL"
}).sort({ created_at: -1 }).limit(10);
```

## Skalierungsüberlegungen

- **Sharding**: Nach `category` oder `database_type` für horizontale Skalierung
- **Replica Sets**: Mindestens 3 Nodes für Ausfallsicherheit
- **Backup**: Tägliche Backups zu S3/Cloud Storage
- **TTL-Index**: Auf `expires_at` für automatisches Löschen veralteter Einträge

## Performance-Tipps

- Embedding-Vektoren für Semantic Search nutzen
- Text-Indizes für Volltextsuche aktivieren
- Compound-Indizes für häufig kombinierte Filterungen
- Document-Kompression aktivieren für großvolumige Collections

## Chunking-Integration in RAG-Datenbank-Strukturen

### Datenfluss mit Chunking

```

Eingabe-Dokument
↓
[CHUNKING-SCHICHT] ← **05_Chunking_Strategie.md**
├─ Document Splitting (512 Tokens, 50 Token Overlap)
├─ Metadaten-Extraktion (Heading, Section, Page)
└─ Chunk-Liste mit chunk_id, chunk_text, metadata
↓
[EMBEDDING-SCHICHT]
├─ Pro Chunk: Text → Embedding-Vektor generieren
├─ Embedding speichern (z. B. 1536-dim für OpenAI)
└─ Chunk + Embedding gebündelt
↓
[DATENBANK-LAYER]
├─ PostgreSQL: rag_chunks, rag_chunks_embeddings
├─ MongoDB: collections.chunks
└─ Redis: Cache häufig abgerufene Chunks

```

### Logische Struktur eines Chunks

Ein Chunk ist die **atomare Einheit** im RAG-System:

| Feld | Typ | Beispiel | Zweck |
|------|-----|---------|-------|
| `chunk_id` | UUID/String | `"doc_abc_chunk_001"` | Eindeutige Identifizierung |
| `document_id` | UUID | `"doc_abc"` | Rückverweis zum Originaldokument |
| `chunk_index` | Integer | `0, 1, 2, ...` | Position im Dokument (für Rekonstruktion) |
| `chunk_text` | Text | `"Dies ist der Chunk-Text..."` | Der eigentliche Inhalt (bis 512 Tokens) |
| `embedding` | Float[] | `[0.123, -0.456, ...]` | Embedding-Vektor (Dimensionität: 1536 für OpenAI) |
| `metadata` | JSON | `{heading: "2.1", page: 5, section: "Methoden"}` | Strukturelle Informationen |
| `created_at` | Timestamp | `2025-11-28T09:40:00Z` | Audit + Versioning |

---

## Chunking-Konfiguration pro RAG-Instanz

Für verschiedene Datenquellen können unterschiedliche Chunking-Parameter verwendet werden:

```

chunking_profiles:
default:
chunk_size: 512
overlap: 50
separator: "sentence"  \# oder "paragraph", "character"
use_cases: ["general_documents", "web_content"]

dense_technical:
chunk_size: 256
overlap: 25
separator: "sentence"
use_cases: ["code_docs", "technical_specs"]

narrative:
chunk_size: 768
overlap: 100
separator: "paragraph"
use_cases: ["books", "articles", "essays"]

```

Siehe auch: **05_Chunking_Strategie.md** für Details zur Chunking-Implementierung.
