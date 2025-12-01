# Portfolio Prüfung: Data Engineering & NoSQL-Systeme
## Vollständige Dokumentation für das Capstone-Projekt

---

# Teil 1: Grundlagen und Lernziele

## 1.1 Was du am Ende dieses Kurses können wirst

Nach diesem Kurs kannst du:
- **Datenarten analysieren**: Strukturierte, semi-strukturierte Dokumente, Embeddings, Ephemeral State unterscheiden
- **Workloads richtig einordnen**: Session-Data, Dokumente, Metadaten, Vektor-Suche klassifizieren
- **Datenmodelle entwickeln**: Modelle die zu echten Use Cases passen
- **NoSQL-Datenbanken unterscheiden und begründet auswählen**: Document Store, Key-Value Store, Vector Store
- **Mini-RAG-Workflow designen**: Retrieval-Qualität und Speicherstruktur verbinden
- **Architekturentscheidungen dokumentieren**: Alternativen bewerten und begründen

**Kernkompetenz**: Du lernst "Data Engineering Denken" – wie man aus Anforderungen technische Entscheidungen ableitet.

## 1.2 RAG als Leitmotiv

RAG-Systeme sind ideal geeignet, um alle wichtigen NoSQL/Data-Engineering-Fähigkeiten zu lernen:

| RAG-Komponente | NoSQL-Konzept |
|----------------|---------------|
| Dokumente | MongoDB/JSON |
| Chunking & Metadaten | Datenmodellierung |
| Embeddings | Vektor-Indizes |
| Sessions, Rate-Limits, Cache | Key-Value (Redis) |
| Query Paths | Performance, Latenz, Kosten |
| Architektur | Polyglotte Speicherlandschaften |

**Wichtig**: RAG ist hier NICHT das Ziel, sondern das didaktische Fahrzeug für echte Data-Engineering-Entscheidungen.

## 1.3 Der Data-Engineering-Flow

Die einheitliche Struktur für den gesamten Kurs:

1. **Datenarten verstehen** → Was für Daten gibt es?
2. **Workloads analysieren** → Wie intensiv werden sie genutzt?
3. **Datenmodelle entwerfen** → Wie strukturieren wir sie?
4. **DB-Technologie auswählen** → Welche Engine passt?
5. **Systemdesign / Query Paths bauen** → Wie fließen die Daten?
6. **Entscheidungen dokumentieren** → Warum diese Wahl?

---

# Teil 2: Die 12 Golden Nuggets

## NUGGET 1: Datenarten & Zugriffsszenarien

### Kernkonzept
Datenarten beschreiben die Natur der Informationen und bestimmen, wie flexibel, wie groß, wie häufig änderbar und wie verknüpft Daten sind.

### Die 5 Datenarten

#### 1. Strukturierte Daten (klassisch relational)
- **Eigenschaften**: Feste Felder, klare Beziehungen (Joins), ACID-Anforderungen, geringe Größe
- **Beispiele**: Kundendaten, Produktkatalog
- **Typische DB**: PostgreSQL

#### 2. Semi-strukturierte Dokumente (JSON, Text, HTML)
- **Eigenschaften**: Flexible Struktur, Abschnitte, Titel, Fließtext, können groß werden
- **Beispiele**: Produktmanuals, Wissensartikel, Chat-Logs
- **Typische DB**: MongoDB

#### 3. Embeddings (Vektoren)
- **Eigenschaften**: Numerische Repräsentationen, 256–4096 Dimensionen, nur für ANN-Suche
- **Beispiele**: Chunk-Embeddings, Query-Embeddings
- **Typische DB**: pgvector, Pinecone, Milvus

#### 4. Ephemerer Zustand (State)
- **Eigenschaften**: Sehr kurzlebig, extrem schnelle Zugriffe, oft überschrieben oder gelöscht
- **Beispiele**: Session-Kontext, Rate-Limit-Zähler, Retrieval-Cache
- **Typische DB**: Redis

#### 5. Zeitreihen (Events, Logs, Monitoring)
- **Eigenschaften**: Viele kleine, kontinuierliche Writes, strikt zeitlich sortiert, selten aktualisiert
- **Beispiele**: LLM-Latenz-Logs, Fehlermeldungen, Monitoring-Daten
- **Typische DB**: TimescaleDB, InfluxDB

### Die 6 Zugriffsmuster

| Muster | Beschreibung | Beispiel |
|--------|--------------|----------|
| Read-heavy | Viele Reads, wenige Writes | Chunks laden |
| Write-heavy | Viele kontinuierliche Writes | Monitoring-Events |
| Read/Write Mixed | Regelmäßige Reads + Updates | Kundendaten ändern |
| Append-only | Nur hinzufügen, nie überschreiben | Chat-Verlauf |
| Bulk-Ingest | Große Mengen auf einmal | Dokument-Import |
| Ultra-low-latency KV | Zugriffe in wenigen ms | Sessions, Rate-Limits |

### Zugriffsszenarien = Datenart × Zugriffsmuster

Ein Zugriffsszenario ist die präzise Beschreibung, wie ein bestimmtes Objekt im System genutzt wird.

**Beispiele aus Customer-Service-RAG:**

| Objekt | Datenart | Zugriffsmuster | Zugriffsszenario |
|--------|----------|----------------|------------------|
| Chunks | Dokument | read-heavy | Chunk Retrieval für jede Agent-Anfrage |
| Embeddings | Vektor | ANN-Suche | Ähnlichkeitssuche für Top-K Retrieval |
| Session-Kontext | State | ultra-low-latency | Kontext pro Anfrage lesen/aktualisieren |
| Chat-Historie | Dokument | append-only | Nachricht an Verlauf anhängen |
| Kundendaten | Strukturiert | read/write mixed | Profil-Lookup plus Feldänderung |
| Logs | Zeitreihe | write-heavy | Event Logging |

### Capstone-Relevanz
✅ Alle Datenarten korrekt identifizieren  
✅ Zu jedem Objekt das passende Zugriffsmuster festlegen  
✅ Für jedes Objekt ein klares Zugriffsszenario formulieren  
✅ Sauber trennen: Dokument vs. Vektor, persistent vs. ephemeral, append-only vs. update

---

## NUGGET 2: Workloads definieren

### Kernkonzept
Workloads sind die Brücke zwischen "Wie nutzen wir die Daten?" und "Welche DB kann das leisten?"

**Wichtig**: Begriffe wie "hoch", "niedrig", "viel", "selten" sind KEINE Workloads. Workloads brauchen **echte Zahlen**.

### Die 4 Dimensionen eines Workloads

#### 1. Häufigkeit
- Wie oft passiert die Operation?
- Beispiele: 12 Reads/s, 500 Inserts/min, 2 Updates/Tag

#### 2. Parallelität
- Wie viele Nutzer/Requests gleichzeitig?
- Beispiele: 5 aktive Agents, 40 parallele Anfragen, 200 gleichzeitige ANN-Suchen

#### 3. Änderungsintensität
- Wie stark verändern sich die Daten?
- Beispiele: nur lesen, häufiges Überschreiben, Append-only, Bulk-Ingest

#### 4. Kritikalität / Fehlertoleranz
- Was passiert wenn die Operation 200 ms dauert? 3 Sekunden? Verloren geht?

### Workload-Formel

**Workload = erwartete Last × gemessene Leistung**

Beispiel:
- MongoDB kann 750 Reads/s (gemessen)
- Use-Case braucht 360 Reads/s
- → **passt** ✅

Beispiel:
- Postgres schafft 15 Writes/s (gemessen)
- Use-Case braucht 40 Writes/s
- → **passt nicht** ❌ → Modell oder Technologie ändern

### Pflicht-Messungen

| Operation | MongoDB | PostgreSQL |
|-----------|---------|------------|
| Read (einzeln) | X ms | Y ms |
| Write (einzeln) | X ms | Y ms |
| Update | X ms | Y ms |
| Append | X ms | Y ms |
| Bulk Read (100) | X ms | Y ms |
| Bulk Write (100) | X ms | Y ms |

### Customer-Service-RAG Workload-Berechnung

**Basis**: 12 RAG-Requests/s normal, 40 RAG-Requests/s peak

Pro Request:
- 6 Chunks liest
- 1 Kundenprofil liest/ändert
- 1 Nachricht anhängt
- 1 Embedding sucht

**Resultierende Workloads (Peak)**:
- Chunk Reads: 40 × 6 = **240 Reads/s**
- Embedding ANN: **40 ANN-Abfragen/s**
- Chat-Appends: **40 Writes/s**
- Session State: **80–120 kleine Reads/Writes/s**

### Capstone-Relevanz
✅ Für jedes Objekt einen Workload mit konkreten Zahlen ableiten  
✅ Begründen, welche Messwerte du brauchst  
✅ Zeigen, dass deine Entscheidung auf Zahlen basiert

---

## NUGGET 3: Datenbank-Auswahl (Risiko-Management)

### Kernkonzept
**DB-Auswahl ist immer Risiko-Management.** Eine Datenbank ist geeignet, wenn keines der Risiken kritisch wird.

### Die 6 Risiko-Kategorien

| Risiko | Beschreibung |
|--------|--------------|
| Integritätsrisiko | Daten wären inkonsistent oder regelwidrig |
| Workload-Risiko | DB schafft die erwartete Last nicht |
| Latenz-Risiko | Operationen im kritischen Pfad werden zu langsam |
| Modellierungsrisiko | Datenmodell passt nicht zur Engine |
| Operations-Risiko | Betrieb, Backups, Monitoring nicht beherrschbar |
| Evolutions-Risiko | Änderungen am Produkt später fast unmöglich |

### Die 6 Auswahlkriterien

#### 1. Konsistenzanforderungen (ACID vs. eventual)
- **Zentrale Frage**: Muss diese Operation garantiert korrekt sein?
- Ja → PostgreSQL (ACID zwingend)
- Nein → MongoDB oder Redis möglich

**ACID-Eigenschaften**:
- **Atomicity**: Transaktion ganz oder gar nicht
- **Consistency**: Datenbank bleibt in gültigem Zustand
- **Isolation**: Parallele Transaktionen beeinflussen sich nicht
- **Durability**: Bestätigte Daten bleiben erhalten

**Eventual Consistency**: Daten werden irgendwann konsistent, aber nicht sofort garantiert.

#### 2. Workload-Form ("Shape")
- **read-heavy** → Dokumente, Chunks → MongoDB
- **write-heavy** → Logs, Zähler → Redis/Timeseries
- **mixed** → OLTP, Kundendaten → PostgreSQL
- **search-heavy** → Embeddings → pgvector

#### 3. Lastprofil (Load Envelope)
- Normale Last (Requests/s)
- Peak-Last (Spikes x2/x5/x10)
- Bursts (extrem kurze Spitzen)
- Latenzbudget (z.B. < 80 ms pro RAG-Request)

**Typische Durchsatzwerte**:
- PostgreSQL JSONB: ~400 Reads/s
- MongoDB: ~700+ Reads/s
- Redis: >100k Ops/s
- pgvector: 2k–10k ANN/s

#### 4. Kritische Query-Pfade
**Frage**: Welche Schritte müssen IMMER schnell sein?

**Kritisch für User Experience**:
- Redis Rate-Limit (1–5 ms)
- Redis Session-Lookup
- pgvector ANN-Suche (~20–40 ms)
- MongoDB Chunk Reads (~20–50 ms)

**NICHT kritisch**:
- Logging
- Analytik
- Monitoring
- Preprocessing

#### 5. Modellierungsrisiko
- MongoDB wird ineffizient bei vielen Teil-Updates
- Redis kann keine komplexen Queries
- PostgreSQL JSONB ist schlecht für riesige Dokumente
- pgvector wird teuer bei Millionen Vektoren ohne Sharding

#### 6. Operability (Betriebsfähigkeit)
- Kann das Team Backups fahren?
- Sind Upgrades einfach?
- Wie schwer ist Monitoring?
- Ist Hochverfügbarkeit trivial oder komplex?

### Der 5-Schritte-Entscheidungsprozess

1. **Datenobjekte bestimmen** (Nugget 1)
2. **Zugriffsszenarien bestimmen** (Nugget 1)
3. **Workloads quantifizieren** (Nugget 2)
4. **Die 6 Kriterien anwenden** (Nugget 3)
5. **Entscheidung dokumentieren** (Nugget 12)

### Beispiel-Auswahl für Customer-Service-RAG

| Objekt | Konsistenz | Workload | Pfad | Modell | → DB |
|--------|-----------|----------|------|--------|------|
| Kundendaten | Hoch | mixed | kritisch | relational | PostgreSQL |
| Chunks | Gering | read-heavy | kritisch | Dokument | MongoDB |
| Embeddings | Gering | search-heavy | kritisch | Vektoren | pgvector |
| Session/Rate-Limit | Gering | write-heavy | kritisch | Key-Value | Redis |

### Capstone-Relevanz
✅ Die 6 Kriterien auf jedes Objekt anwenden  
✅ Alternativen ausschließen mit Begründung  
✅ Finale Entscheidung dokumentieren

---

## NUGGET 4: Query Paths & Systemkosten

### Kernkonzept
Query Paths bestimmen, welche Operationen im kritischen Pfad liegen und die Latenz dominieren.

### Kritischer Pfad vs. Nicht-kritischer Pfad

**Kritischer Pfad**: Operationen, die direkt die User-Response-Zeit beeinflussen
- Müssen optimiert werden
- Latenzbudget ist hart
- Fehler/Verzögerungen sind sofort spürbar

**Nicht-kritischer Pfad**: Operationen im Hintergrund
- Können asynchron laufen
- Höhere Latenz akzeptabel
- Eventual consistency oft ausreichend

### Latenzbudget-Planung

**Beispiel RAG-Request (Ziel: < 500 ms)**:
- Rate-Limit Check: 2 ms (Redis)
- Session Lookup: 3 ms (Redis)
- Query Embedding: 50 ms (API)
- ANN Search: 30 ms (pgvector)
- Chunk Retrieval: 40 ms (MongoDB)
- LLM Generation: 300 ms (API)
- **Total**: ~425 ms ✅

### Systemkosten-Faktoren

| Faktor | Einfluss auf Kosten |
|--------|---------------------|
| Anzahl DB-Calls | Mehr Calls = mehr Latenz |
| Datenmenge pro Call | Größere Payloads = mehr I/O |
| Index-Nutzung | Ohne Index = Full Scan |
| Netzwerk-Hops | Mehr Hops = mehr Latenz |
| Caching-Effizienz | Cache Hit = schnell, Miss = langsam |

---

## NUGGET 5: Datenmodellierung nach Access Paths

### Kernkonzept
NoSQL = Modell folgt dem Use-Case, nicht umgekehrt. Im Gegensatz zu relationalen Datenbanken designst du das Datenmodell nach den Zugriffsmustern.

### Denormalisierung in NoSQL

**Relationales Denken**: Daten normalisieren, Redundanz vermeiden, Joins nutzen
**NoSQL-Denken**: Daten so speichern, wie sie gelesen werden, Redundanz akzeptieren

### MongoDB-Schema-Design-Patterns

#### Embedded Documents
```json
{
  "article_id": "123",
  "title": "MongoDB Basics",
  "author": {
    "name": "Max Mustermann",
    "email": "max@example.com"
  },
  "tags": ["NoSQL", "Database", "Tutorial"]
}
```

**Wann verwenden**: Wenn Daten zusammen gelesen werden

#### References
```json
// Artikel
{ "_id": "article_123", "title": "MongoDB Basics", "author_id": "user_456" }

// User
{ "_id": "user_456", "name": "Max Mustermann" }
```

**Wann verwenden**: Bei großen, unabhängig aktualisierten Entitäten

### Design-Entscheidungen

| Frage | Embedded | Reference |
|-------|----------|-----------|
| Werden Daten zusammen gelesen? | ✅ | ❌ |
| Sind Sub-Dokumente groß? | ❌ | ✅ |
| Werden Sub-Daten oft geändert? | ❌ | ✅ |
| Gibt es 1:n mit großem n? | ❌ | ✅ |

---

## NUGGET 6: Chunking als Datenmodellierung

### Kernkonzept
Chunking ist nicht "Textschneiden", sondern Datenmodellierung. Wie du Dokumente schneidest, bestimmt die Retrieval-Qualität.

### Chunking-Strategien

#### 1. Fixed-Size Chunking
- Feste Anzahl Tokens/Zeichen pro Chunk
- Einfach zu implementieren
- Kann semantische Einheiten zerstören

```
Chunk 1: [0-500 tokens]
Chunk 2: [500-1000 tokens]
...
```

#### 2. Semantic Chunking
- Chunks an natürlichen Grenzen (Absätze, Überschriften)
- Erhält semantische Kohärenz
- Variable Chunk-Größe

#### 3. Overlapping Chunks
- Chunks überlappen um X%
- Verhindert Informationsverlust an Grenzen
- Erhöht Speicherbedarf

**Typische Konfiguration**: 256-512 Tokens mit 10-20% Overlap

### Chunking-Datenmodell

```json
{
  "chunk_id": "doc_001_chunk_003",
  "document_id": "doc_001",
  "content": "...",
  "position": 3,
  "metadata": {
    "section": "Introduction",
    "page": 2,
    "word_count": 450
  },
  "embedding_ref": "emb_001_003"
}
```

### Chunking-Workload-Beziehung

| Chunk-Größe | Read-Workload | Retrieval-Qualität | Embedding-Kosten |
|-------------|---------------|-------------------|------------------|
| Klein (100 Token) | Hoch (viele Chunks) | Hoch (präzise) | Hoch |
| Mittel (500 Token) | Mittel | Mittel | Mittel |
| Groß (1000+ Token) | Niedrig | Niedrig (unscharf) | Niedrig |

---

## NUGGET 7: Embeddings als eigener Datentyp

### Kernkonzept
Embeddings sind ein eigener Datentyp mit eigenem Workload. Sie erfordern spezielle Indizes und Suchalgorithmen.

### Embedding-Eigenschaften

- **Dimensionalität**: Typisch 256–4096 Dimensionen
- **Speicherbedarf**: 1536 Dim × 4 Bytes = ~6 KB pro Embedding
- **Operationen**: Nur Ähnlichkeitssuche (ANN), keine regulären Queries

### ANN-Algorithmen

#### HNSW (Hierarchical Navigable Small World)
- Graph-basierte Suche
- Sehr schnelle Queries
- Höherer Speicherbedarf
- Gute Performance bei Updates

**Parameter**:
- `m`: Anzahl Nachbarn pro Knoten (Standard: 16)
- `ef_construction`: Suchbreite beim Aufbau (Standard: 64-200)
- `ef_search`: Kandidaten bei Suche (Standard: 40-100)

#### IVFFlat (Inverted File with Flat)
- Cluster-basierte Suche
- Schneller Index-Aufbau
- Geringerer Speicherbedarf
- Performance degradiert bei Updates

**Parameter**:
- `lists`: Anzahl Cluster (√n bis n/1000)
- `probes`: Anzahl durchsuchter Cluster

### HNSW vs. IVFFlat Vergleich

| Aspekt | HNSW | IVFFlat |
|--------|------|---------|
| Build-Zeit | Langsam (~32x) | Schnell |
| Speicher | Hoch (~2.8x) | Niedrig |
| Query-Speed | Sehr schnell (~15x) | Langsamer |
| Update-Toleranz | Hoch | Niedrig |

**Empfehlung**:
- **HNSW**: Für dynamische Daten, schnelle Queries
- **IVFFlat**: Für statische Daten, Speichereffizienz

### pgvector Beispiel

```sql
-- Extension aktivieren
CREATE EXTENSION vector;

-- Tabelle mit Embedding-Spalte
CREATE TABLE embeddings (
  id SERIAL PRIMARY KEY,
  chunk_id VARCHAR(100),
  embedding vector(1536)
);

-- HNSW Index erstellen
CREATE INDEX ON embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);

-- ANN-Suche
SELECT chunk_id, embedding <=> '[0.1, 0.2, ...]' AS distance
FROM embeddings
ORDER BY distance
LIMIT 10;
```

---

## NUGGET 8: Metadaten als First-Class-Citizen

### Kernkonzept
Gute Metadaten reduzieren Komplexität und beschleunigen Retrieval. Metadaten sind nicht optional, sondern zentral.

### Metadaten-Kategorien

#### 1. Strukturelle Metadaten
- Dokument-ID, Chunk-Position, Section, Page

#### 2. Inhaltliche Metadaten
- Thema, Kategorie, Schlüsselwörter, Sprache

#### 3. Temporale Metadaten
- Erstellungsdatum, Änderungsdatum, Gültigkeitszeitraum

#### 4. Prozess-Metadaten
- Embedding-Modell, Chunk-Strategie, Version

### Metadaten-gesteuertes Retrieval

**Pre-Filtering**: Metadaten filtern VOR der Vektor-Suche
```sql
SELECT * FROM embeddings
WHERE category = 'technical'
  AND created_at > '2024-01-01'
ORDER BY embedding <=> query_vector
LIMIT 10;
```

**Post-Filtering**: Metadaten filtern NACH der Vektor-Suche
- Erst Top-K aus Vektor-Suche holen
- Dann Metadaten-Filter anwenden

### Metadaten-Schema-Beispiel

```json
{
  "chunk_id": "doc_001_chunk_003",
  "content": "...",
  "metadata": {
    "source_document": "product_manual_v2.pdf",
    "document_type": "manual",
    "product_category": "coffee_machines",
    "language": "de",
    "created_at": "2024-01-15",
    "section_title": "Troubleshooting",
    "page_number": 42,
    "embedding_model": "text-embedding-3-small",
    "chunk_strategy": "semantic_500_overlap_50"
  }
}
```

---

## NUGGET 9: Retrieval als Query-Design

### Kernkonzept
Retrieval ist keine Magie, sondern eine Abfolge konkreter Datenbankzugriffe, die designed werden müssen.

### Retrieval-Pipeline Schritte

1. **Query Understanding**: User-Input analysieren
2. **Query Embedding**: Text in Vektor umwandeln
3. **Candidate Retrieval**: Top-K aus Vektor-DB
4. **Re-Ranking**: Kandidaten neu sortieren
5. **Context Assembly**: Relevante Chunks zusammenstellen
6. **Generation**: LLM-Antwort generieren

### Retrieval-Strategien

#### Simple Retrieval
- Ein Embedding-Query
- Top-K direkt nutzen

#### Hybrid Retrieval
- Kombination aus Vektor-Suche und Keyword-Suche
- Bessere Abdeckung

#### Multi-Query Retrieval
- Query in mehrere Sub-Queries aufteilen
- Ergebnisse zusammenführen

### Query-Design-Entscheidungen

| Entscheidung | Trade-off |
|--------------|-----------|
| Top-K Größe | Mehr K = bessere Abdeckung, mehr Kosten |
| Similarity Threshold | Strenger = präziser, weniger Ergebnisse |
| Re-Ranking | Besser = genauer, mehr Latenz |
| Metadata Filter | Mehr Filter = präziser, weniger Ergebnisse |

---

## NUGGET 10: Polyglotte Speicher (Document + Vector + KV)

### Kernkonzept
Moderne Systeme nutzen mehrere spezialisierte Datenbanken. Das ist keine Schwäche, sondern rationale Trennung nach Workloads.

### Die Mindestarchitektur

```
┌─────────────────────────────────────────────────────┐
│                    Anwendung                        │
└─────────────────────────────────────────────────────┘
        │                │                │
        ▼                ▼                ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   MongoDB     │ │   pgvector    │ │    Redis      │
│  (Dokumente)  │ │  (Vektoren)   │ │ (Session/KV)  │
└───────────────┘ └───────────────┘ └───────────────┘
```

### Warum polyglott?

| Single-DB | Polyglott |
|-----------|-----------|
| Einfacher Betrieb | Optimale Performance je Workload |
| Ein Skillset | Spezialisierte Engines |
| Konsistenz einfach | Konsistenz über DBs komplex |
| Feature-Kompromisse | Best-of-Breed |

### Synchronisation in polyglotten Systemen

**Herausforderung**: Daten müssen über mehrere DBs konsistent bleiben

**Strategien**:
1. **Eventual Consistency**: Asynchrone Updates, irgendwann konsistent
2. **Saga Pattern**: Verteilte Transaktionen als Schrittfolge
3. **Event Sourcing**: Alle Änderungen als Events, DBs als Projektionen
4. **Outbox Pattern**: Änderungen in Outbox-Tabelle, dann async verteilen

### Praxis-Empfehlungen

| Workload | Empfohlene DB | Begründung |
|----------|---------------|------------|
| Dokumente, Chunks | MongoDB | Flexible Schemas, read-heavy |
| Embeddings, ANN | pgvector | In PostgreSQL integriert |
| Sessions, Rate-Limits | Redis | Sub-ms Latenz, TTL |
| Strukturierte Daten | PostgreSQL | ACID, Joins |
| Logs, Monitoring | TimescaleDB | Time-series optimiert |

---

## NUGGET 11: Einfachheit im Prototyping

### Kernkonzept
Keep it simple: Jede Schicht zu früh zu optimieren macht alles schlechter.

### Die Prototyping-Maximen

1. **Start simple**: Erst beweisen, dass der Use-Case funktioniert
2. **Measure first**: Keine Optimierung ohne Messwerte
3. **Optimize bottlenecks**: Nur den kritischen Pfad optimieren
4. **Avoid premature complexity**: Sharding, Clustering etc. erst wenn nötig

### Prototyp vs. Produktion

| Aspekt | Prototyp | Produktion |
|--------|----------|------------|
| Hosting | Lokal/Docker | Cloud/Managed |
| Skalierung | Single Node | Clustering |
| Monitoring | Basic Logs | Full Observability |
| Backups | Optional | Pflicht |
| Security | Minimal | Full Compliance |

### Wann ist es "gut genug"?

- Funktionalität bewiesen
- Latenz im Budget
- Workload geschafft
- Engpässe identifiziert

**Dann erst**: Produktionshärtung

---

## NUGGET 12: Dokumentierte Entscheidungen

### Kernkonzept
Data Engineering = dokumentierte Entscheidungen. Transparenz, Alternativen, Risiken, Begründung.

### Architecture Decision Record (ADR)

**Template**:
```
# ADR-001: Wahl des Document Stores

## Status
Akzeptiert

## Kontext
Wir brauchen einen Speicher für semi-strukturierte Dokumente 
(Chunks, Wissensartikel) mit read-heavy Workload.

## Entscheidung
Wir wählen MongoDB.

## Alternativen betrachtet
1. PostgreSQL JSONB
   - Pro: Bereits im Stack
   - Contra: Grenzwertig bei 240 Reads/s
   
2. Elasticsearch
   - Pro: Volltextsuche
   - Contra: Overkill, höherer Betriebsaufwand

## Konsequenzen
- MongoDB zu Skillset hinzufügen
- Separate Backup-Strategie
- Eventual Consistency akzeptieren

## Risiken
- Workload-Risiko: Gering (gemessen 700+ Reads/s)
- Operations-Risiko: Mittel (neues Tool)
```

### Was dokumentiert werden muss

✅ Datenobjekte und ihre Klassifizierung  
✅ Zugriffsszenarien für jedes Objekt  
✅ Workloads mit konkreten Zahlen  
✅ Messwerte aus Tests  
✅ Angewandte Auswahlkriterien  
✅ Betrachtete Alternativen  
✅ Begründung der finalen Wahl  
✅ Identifizierte Risiken  
✅ Akzeptierte Trade-offs

---

# Teil 3: Capstone-Projekt

## Anforderungen

Du entwirfst ein Mini-RAG-System zum Thema Datenbanken, inklusive:

1. **Dokumentmodell**: Wie sind Dokumente strukturiert?
2. **Chunkingmodell**: Wie werden Dokumente aufgeteilt?
3. **Embeddingspeicher**: Wie werden Vektoren gespeichert/indiziert?
4. **Retrieval-Flow**: Wie läuft eine Anfrage ab?
5. **Begründeter Einsatz von mind. 2 NoSQL-Technologien**
6. **Schriftliche Ausarbeitung**
7. **20-minütige Präsentation**

## Bewertungskriterien

| Kriterium | Gewicht |
|-----------|---------|
| Datenarten korrekt identifiziert | ✓ |
| Workloads richtig zugeordnet | ✓ |
| Chunking + Metadaten sauber modelliert | ✓ |
| Vektor-Speicher begründet ausgewählt | ✓ |
| Ephemeral State korrekt getrennt | ✓ |
| Query Paths nachvollziehbar beschrieben | ✓ |
| Alternativen erkannt und bewertet | ✓ |
| Begründete Entscheidungen dokumentiert | ✓ |

## Capstone-Checkliste

### Phase 1: Analyse
- [ ] Alle Datenobjekte identifiziert
- [ ] Datenarten zugeordnet
- [ ] Zugriffsmuster bestimmt
- [ ] Zugriffsszenarien formuliert

### Phase 2: Workloads
- [ ] Erwartete Last berechnet (Requests/s)
- [ ] Messwerte erhoben (Reads, Writes, Latenz)
- [ ] Kritische Pfade identifiziert
- [ ] Latenzbudgets definiert

### Phase 3: Design
- [ ] Datenmodelle entworfen
- [ ] Chunking-Strategie gewählt
- [ ] Metadaten-Schema definiert
- [ ] Index-Strategie festgelegt

### Phase 4: DB-Auswahl
- [ ] 6 Kriterien angewandt
- [ ] Alternativen dokumentiert
- [ ] Risiken bewertet
- [ ] Finale Wahl begründet

### Phase 5: Dokumentation
- [ ] ADRs geschrieben
- [ ] System-Diagramm erstellt
- [ ] Query-Flow dokumentiert
- [ ] Trade-offs erklärt

---

# Teil 4: Glossar

| Begriff | Definition |
|---------|------------|
| **ACID** | Atomicity, Consistency, Isolation, Durability - Transaktionseigenschaften |
| **ANN** | Approximate Nearest Neighbor - approximierte Ähnlichkeitssuche |
| **Chunking** | Aufteilung von Dokumenten in kleinere Einheiten |
| **Document Store** | DB für semi-strukturierte Dokumente (JSON/BSON) |
| **Embedding** | Numerische Vektorrepräsentation von Text |
| **Ephemeral State** | Kurzlebige Daten (Sessions, Cache) |
| **Eventual Consistency** | Daten werden irgendwann konsistent |
| **HNSW** | Hierarchical Navigable Small World - Graph-basierter ANN-Index |
| **IVFFlat** | Inverted File Flat - Cluster-basierter ANN-Index |
| **Key-Value Store** | Einfachste NoSQL-Form (Schlüssel-Wert-Paare) |
| **Latenzbudget** | Maximal erlaubte Zeit für eine Operation |
| **Polyglot Persistence** | Nutzung mehrerer DB-Technologien |
| **Query Path** | Abfolge von DB-Operationen für eine Anfrage |
| **RAG** | Retrieval-Augmented Generation |
| **TTL** | Time-To-Live - automatische Datenlöschung |
| **Vector Store** | DB optimiert für Vektor-Ähnlichkeitssuche |
| **Workload** | Quantifizierte Last auf einem System |

---

# Teil 5: Beispiel-Lösungen

## Mini-Aufgabe Modul 1

| Objekt | Datenart | Zugriffsmuster | Zugriffsszenario |
|--------|----------|----------------|------------------|
| A) Troubleshooting-Manual | Dokument | read-heavy | Chunk Retrieval für Support-Anfragen |
| B) Embedding chunk_42 | Vektor | ANN-Suche | Ähnlichkeitssuche für Retrieval |
| C) Rate-Limit Counter | Ephemerer State | ultra-low-latency | Request-Zählung mit TTL |
| D) Kundenprofil | Strukturiert | read/write mixed | Profil laden und aktualisieren |
| E) Chat-Verlauf | Dokument | append-only | Nachrichten anhängen |

## Mini-Aufgabe Modul 2

**Aussagen-Bewertung**:

| Aussage | Bewertung | Warum |
|---------|-----------|-------|
| "Mongo ist schneller als Postgres" | ❌ wertlos | Ohne Zahlen nutzlos |
| "Mongo: 2.1 ms Read, Postgres: 4.8 ms" | ✅ nützlich | Direkt vergleichbar |
| "Chats sind Append-only" | ✅ nützlich | Beeinflusst Modell & Last |
| "Use-Case hat viele Reads" | ❌ wertlos | Keine Zahl = kein Workload |

---

**Viel Erfolg bei deiner Portfolio-Prüfung!**

*Diese Dokumentation basiert auf dem DHBW Lörrach Kurs "Data Engineering & NoSQL-Systeme"*
