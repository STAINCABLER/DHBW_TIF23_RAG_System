# Portfolio: Der Datenbank Design Deputy (DDDD)

**Projekt:** DHBW TIF23 RAG-System  
**Datum:** Dezember 2025  
**Thema:** Retrieval-Augmented Generation für Datenbankberatung bei Startups und KMU
**Matrikelnummer:** 3230442 1837738 8317319 7083848

---

## Inhaltsverzeichnis

1. [Ziel & Use Case](#1-ziel--use-case)
2. [Dokumentenauswahl + Datenbasis](#2-dokumentenauswahl--datenbasis)
3. [Chunking-Design](#3-chunking-design)
4. [Datenmodell](#4-datenmodell)
5. [Speicherarchitektur](#5-speicherarchitektur)
6. [Retrieval-Flow](#6-retrieval-flow)
7. [Tests & Beispiele](#7-tests--beispiele)
8. [Reflexion](#8-reflexion)

---

## 1. Ziel & Use Case

### 1.1 Zielsetzung: Der Datenbank Design Deputy

Das entwickelte RAG-System - **„Der Datenbank Design Deputy"** - dient als intelligenter Beratungsassistent für **Startups und kleine lokale Unternehmen (KMU)**, die ihre IT-Infrastruktur erstmalig aufbauen oder erweitern möchten. Diese Zielgruppe verfügt häufig über begrenzte Ressourcen und fehlendes Fachwissen im Bereich Datenbankarchitektur, benötigt aber dennoch fundierte Entscheidungsgrundlagen.

**Primäres Ziel:**
- Unterstützung von Gründern und technischen Leitern bei der Auswahl und Gestaltung einer passenden Datenbankarchitektur
- Bereitstellung von Best Practices und Entscheidungshilfen durch semantische Suche in kuratierten Fachmaterialien

### 1.2 Zielgruppe und deren Herausforderungen

| Zielgruppe | Typische Herausforderung |
|------------|--------------------------|
| **Tech-Startups** | Schnelle Skalierung, unklare Anforderungen |
| **Lokale Einzelhändler** | Kundendaten, Inventar, wenig IT-Budget |
| **Handwerksbetriebe** | Auftragsverwaltung, Terminplanung |
| **Freiberufler/Agenturen** | Projektdaten, Kundenverwaltung |

### 1.3 Art der zu beantwortenden Fragen

Das System ist optimiert für praxisorientierte Fragetypen, die typisch für Infrastruktur-Einsteiger sind:

| Fragetyp | Beispiel |
|----------|----------|
| **Grundlagenverständnis** | „Was ist der Unterschied zwischen SQL und NoSQL?" |
| **Technologieauswahl** | „Welche Datenbank eignet sich für meinen Online-Shop?" |
| **Skalierungsfragen** | „Wie bereite ich meine Datenbank auf Wachstum vor?" |
| **Kostenoptimierung** | „Brauche ich wirklich eine separate Vektor-Datenbank?" |
| **Best Practices** | „Wie strukturiere ich Kundendaten richtig?" |
| **Architekturentscheidung** | „Wann ist eventual consistency für mein Startup akzeptabel?" |

---

## 2. Dokumentenauswahl & Datenbasis

### 2.1 Unterstützte Dokumentformate

Das System unterstützt **vier Dokumentformate**, die jeweils unterschiedliche Anwendungsfälle und Strukturierungsgrade abdecken:

| Format | Dateiendung | Typischer Inhalt | Chunking-Strategie |
|--------|-------------|------------------|-------------------|
| **Markdown** | `.md` | Strukturierte Fachtexte mit Überschriften | Heading-Aware (##) |
| **JSON** | `.json` | Strukturierte Key-Value-Daten, Glossare | Top-Level-Key-Split/ Element-Split |
| **CSV** | `.csv` | Tabellarische Daten, Vergleichsmatrizen | Zeilen-Batching (5er) |
| **Text** | `.txt` | Semistrukturierte Fließtexte mit Absätzen | Absatz-basiert (10% Overlap) |

#### Begründung der Formatauswahl

**Markdown (.md):**
- Ideal für Fachdokumentation mit natürlicher Gliederung
- `##`-Überschriften definieren semantische Einheiten
- Ermöglicht automatische Extraktion von Abschnittstiteln als Metadaten

**JSON (.json):**
- Geeignet für strukturierte Wissensdaten (Glossare, Q&A-Paare, Regelsätze)
- Jeder Top-Level-Key/ jedes Element repräsentiert ein abgeschlossenes Konzept
- Maschinenlesbar und eindeutig parsbar

**CSV (.csv):**
- Optimal für tabellarische Vergleichsdaten (z.B. Isolation-Level-Matrix)
- Zeilen enthalten zusammengehörige Datensätze
- Batch-Verarbeitung erhält tabellarischen Kontext

**Text (.txt):**
- Semistrukturierte Inhalte mit impliziter Gliederung durch Absätze (Leerzeilen)
- Absatz-basiertes Chunking mit **10% Overlap** zu Vorgänger- und Nachfolger-Chunk
- Overlap verhindert Kontextverlust an Absatzgrenzen bei längeren Fließtexten

### 2.2 Auswahlkriterien für Dokumente

Die Dokumentenauswahl folgt folgenden Prinzipien:

1. **Semantische Kohärenz:** Jedes Dokument behandelt ein abgeschlossenes Themengebiet
2. **Strukturierte Abschnitte:** Markdown-Überschriften bzw. Absatztrennungen in Text Dateien, ermöglichen Heading-Aware Chunking
3. **Variabilität der Formate:** Verschiedene Formate decken unterschiedliche Chunking-Strategien ab

---

## 3. Chunking-Design

### 3.1 Chunking-Strategien

Das System implementiert **drei formatspezifische Chunking-Strategien**, die jeweils auf die Struktur der Eingabedokumente abgestimmt sind. Jede Strategie erzeugt semantisch kohärente Chunks mit vollständigen Metadaten.

#### 3.1.1 Markdown-Chunking: Heading-Aware Strategie

**Datei:** `setup/chunks/md_chunker.py`

Markdown-Dokumente werden anhand ihrer Überschriftenhierarchie in Chunks zerlegt. Diese Strategie nutzt den `MarkdownHeaderTextSplitter` aus LangChain:

```python
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]
    markdown_splitter = langchain_text_splitters.MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
```

**Funktionsweise:**
- Jeder Abschnitt (definiert durch `##`) wird ein eigenständiger Chunk
- Der Text zwischen zwei `##`-Überschriften bildet einen zusammenhängenden Chunk
- `Header 1` wird zusätzlich extrahiert, also auch als Chunk-Trenner verwendet. Um auch die Überschrift und Text zwischen Header 1 und dem ersten Header 2 zu berücksichtigen
- Das Embedding wird aus der Kombination `{header_1_info}-{header_info}: {content}`, also `Überschrift-Abschnitt: Content` erzeugt

**Begründung für Chunking Strategie:**
- H1 (`#`) dient typischerweise als Dokumenttitel, hat jedoch teils zusätzlich Text nachgestellt
- H2 (`##`) repräsentiert in unseren Dokumenten die thematischen Hauptabschnitte
- H3 (`###`) würde zu kleine, fragmentierte Chunks erzeugen

**Vorteile:**
- Chunks entsprechen natürlichen semantischen Einheiten
- Keine willkürliche Fragmentierung von Erklärungen
- Überschriften liefern wertvolle Metadaten für das Retrieval

#### 3.1.2 JSON-Chunking: Key-Value Strategie

**Datei:** `setup/chunks/json_chunker.py`

JSON-Dokumente werden auf oberster Ebene nach Schlüsseln aufgeteilt - jeder Key wird zu einem eigenständigen Chunk:

```python
    if isinstance(data, dict):
        value = data[key]
    else:
        value = key
        key = ""

    content: str = json.dumps(value)

    tensor: torch.Tensor = util.embedding.build_embedding(f"{key}: {content}")
```

**Funktionsweise:**
- Iteration über alle Top-Level-Keys des JSON-Objekts
- Iteration über alle Elemente bei JSON-Arrays
- Jeder Key-Value-Paar/Element wird ein Chunk
- Der Key (falls vorhanden) wird als `heading`-Metadatum gespeichert
- Das Embedding kombiniert Key und Value für kontextreichere Vektoren

#### 3.1.3 CSV-Chunking: Batch-Strategie

**Datei:** `setup/chunks/csv_chunker.py`

CSV-Dateien werden zeilenweise eingelesen und in Batches von 5 Zeilen gruppiert:

```python
def batching(data, batch_size):
    current_datas: list = []
    current_size: int = 0
    for i in data:
        current_datas.append(i)
        current_size += 1
        if current_size >= batch_size:
            yield current_datas
            current_datas = []
            current_size = 0
    if current_size > 0:
        yield current_datas

def chunk_csv(content: list[dict[str, any]], file_name: str) -> None:
    for i, batch in enumerate(batching(content, 5)):
        content: str = json.dumps(batch)
        tensor = util.embedding.build_embedding(content)
```

**Funktionsweise:**
- CSV wird als Liste von Dictionaries eingelesen (`csv.DictReader`)
- Zeilen werden in Batches à 5 Einträge gruppiert
- Jeder Batch wird als JSON-String serialisiert und embeddet
- Der Dateiname dient als `heading`-Metadatum

**Begründung der Batch-Größe:**
- **Batch-Size 5:** Verhindert zu kleine Chunks bei tabellarischen Daten (z.B. Isolation-Level-Matrix mit wenigen Zeilen)
- Tabellarische Daten sind oft nur im Zusammenhang verständlich (z.B. Vergleich mehrerer Join-Typen)

#### 3.1.4 Text-Chunking: Absatz-basierte Strategie mit Overlap

**Datei:** `setup/chunks/txt_chunker.py`

Textdateien werden anhand von Absätzen (Leerzeilen) in Chunks zerlegt. Da Absätze in Fließtexten semantische Einheiten darstellen, nutzt diese Strategie die natürliche Gliederung. Zusätzlich wird ein **10% Overlap** implementiert:

```python
    if "\r\n" in data:
        raw_data: list[str] = data.split("\r\n\r\n")
    else:
        raw_data: list[str] = data.split("\n\n")

    for i, raw_text in enumerate(raw_data):

        previous_text: str = ""
        next_text: str = ""

        if i > 0:
            previous_raw_text: str = raw_data[i - 1]
            first_char_index: int = int(len(previous_raw_text) * 0.9)

            first_char_index: int = previous_raw_text.find(" ", first_char_index)
            if first_char_index > 0:
                previous_text = previous_raw_text[first_char_index:]
        
        if i < len(raw_data) - 1:
            next_raw_text: str = raw_data[i + 1]
            first_char_index: int = int(len(next_raw_text) * 0.1)

            first_char_index: int = next_raw_text.find(" ", first_char_index)
            if first_char_index > 0:
                next_text = next_raw_text[:first_char_index]
        
        full_text: str = f"{previous_text}\n{raw_text}\n{next_text}"

        if "\r\n" in raw_text:
            section_name: str = raw_text.split("\r\n")[0]
        else:
             section_name: str = raw_text.split("\n")[0]

        tensor: torch.Tensor = util.embedding.build_embedding(f"{main_title}-{section_name}: {full_text}")
```

**Funktionsweise:**
- Text wird bei doppelten Zeilenumbrüchen (`\n\n`) in Absätze zerlegt
- Jeder Absatz bildet einen Chunk
- Chunks enthalten 10% des vorherigen und 10% des nachfolgenden Absatzes als Overlap und trennt bei bestehendem Leerzeichen (falls besteht)
- Die erste Zeile des Dokuments, kombiniert mit der ersten Zeile eines Chunks, dient als `heading`-Metadatum

**Begründung für Absatz-Split:**
- **Natürliche Struktur:** Absätze in Fließtexten repräsentieren thematische Einheiten
- **Semistrukturiert:** TXT-Dateien sind nicht "unstrukturiert" - Leerzeilen bieten implizite Gliederung
- **Semantische Kohärenz:** Ein Absatz behandelt typischerweise einen Gedanken

**Begründung für 0% Overlap bei Markdown, JSON und CSV:**
- **Klare Grenzen:** Diese Formate haben explizite Strukturen (Überschriften, Keys, Zeilen)
- **Redundanz vermeiden:** Overlap würde unnötige Duplikate erzeugen
- **Kontext durch Metadaten:** Überschriften und Keys liefern ausreichend Kontext

**Begründung für 10% Overlap bei Text:**
- **Kontextübergänge:** Absätze können aufeinander Bezug nehmen
- **Satzfortsetzungen:** Manche Gedanken spannen sich über Absatzgrenzen
- **Kompromiss:** 10% ist gering genug um Redundanz zu minimieren, aber ausreichend für Kontexterhaltung

### 3.2 Übersicht der Chunking-Strategien

| Format | Strategie | Chunk-Einheit | Metadaten-Quelle | Overlap |
|--------|-----------|---------------|------------------|---------|
| **Markdown** | Heading-Aware | Abschnitt (##) | Header 2 | 0% |
| **JSON** | Key-Value | Top-Level-Key/Element | Key-Name | 0% |
| **CSV** | Batching | 5 Zeilen pro Chunk | Dateiname | 0% |
| **Text** | Absatz-basiert | Paragraph (\n\n) | Dateititel + Absatzanfang | 10% |

### 3.3 Embedding-Umsetzung

#### 3.3.1 Embedding-Modell

**Datei:** `util/embedding.py`

Das System verwendet das Sentence-Transformer-Modell `all-MiniLM-L6-v2` zur Vektorisierung:

```python
import sentence_transformers
import torch

DEFAULT_MODEL = "all-MiniLM-L6-v2"

model: sentence_transformers.SentenceTransformer = sentence_transformers.SentenceTransformer(DEFAULT_MODEL)

def build_embedding(content: str) -> torch.Tensor:
    return model.encode(content)
```

#### 3.3.2 Modellcharakteristik

| Eigenschaft | Wert | Bedeutung |
|-------------|------|-----------|
| **Dimensionalität** | 384 | Kompakter Vektor, speichereffizient |
| **Modellgröße** | ~90 MB | Schnelles Laden, geringer Ressourcenbedarf |
| **Max. Sequenzlänge** | By default 256 Wörter | Ausreichend für unsere Chunk-Größen |
| **Trainingsgrundlage** | Sentence-Pairs | Optimiert für semantische Ähnlichkeit |

**Begründung der Modellwahl:**
- **Geschwindigkeit:** Das Modell ist klein genug für lokale Inferenz ohne GPU
- **Qualität:** Trotz geringer Größe liefert es gute semantische Repräsentationen für Fachtexte
- **Mehrsprachigkeit:** Unterstützt Deutsch und Englisch, was für unsere gemischten Dokumente relevant ist

#### 3.3.3 Vektor-Speicherung

Die generierten Embeddings werden als Float-Array direkt in einem Chunk-Dokument gespeichert:

```python
vector: pgvector.psycopg2.vector.Vector = pgvector.psycopg2.vector.Vector(tensor)

chunk: dict[str, any] = {
    # ... andere Felder ...
    "embedding": vector.to_list(),  # 384-dimensionaler Float-Vektor
}
```

### 3.4 Ingest-Performance

Der gesamte Chunking- und Embedding-Prozess für alle Grundwissen-Dateien wurde gemessen:

| Metrik | Wert |
|--------|------|
| **Gesamtdauer** | **230,74 Sekunden** (~3,8 Minuten) |
| **Verarbeitete Dokumente** | 89 |
| **Erzeugte Chunks** | ~11850 |
| **Ø Zeit pro Dokument** | ~2,59 Sekunden |
| **Ø Zeit pro Chunk** | ~0,019 Sekunden |

**Hinweis:** Die Ingest-Zeit ist ein **einmaliger Aufwand** beim Setup. Zur Laufzeit werden nur vorberechnete Embeddings aus MongoDB geladen.

### 3.5 Beispiel: Guter vs. Schlechter Chunk

#### Guter Chunk :)

```json
{
  "chunk_id": "c7a3f2e1-...",
  "document_id": "doc_nosql_overview",
  "chunk_index": 2,
  "chunk_text": "Dokumentenorientierte Datenbanken speichern Dokumente (oft JSON/BSON) mit variabler Struktur. Sammlungen (Collections) statt Tabellen. Stärken: Flexibles Schema (Schema-on-Read), gute Unterstützung für verschachtelte Strukturen und Aggregationspipelines. Typische Use-Cases: Content-Management, Benutzerprofile, Produktkataloge.",
  "metadata": {
    "heading": "Dokumentenorientierte Datenbanken",
    "section": "3",
    "source_file": "db_nosql_models_overview.md"
  }
}
```

**Warum gut:**
- **Semantisch kohärent:** Behandelt genau ein Thema (Document Stores)
- **Vollständig:** Enthält Definition, Stärken und Use-Cases
- **Metadaten vorhanden:** `section_title` ermöglicht kontextbezogene Suche
- **Richtige Größe:** ~80 Wörter, ausreichend für präzise Antworten

#### Schlechter Chunk :(

```json
{
  "chunk_id": "bad_chunk_001",
  "chunk_text": "Typische Use-Cases: Content-Management, Benutzerprofile, Produktkataloge. Beispiele: MongoDB, CouchDB. ## 4. Spaltenfamilien-/Wide-Column-Stores Datenmodell: Mehrdimensionale Key-Value-Struktur mit Zeilenkey",
  "metadata": {}
}
```

**Warum schlecht:**
- **Semantisch inkohärent:** Vermischt zwei verschiedene NoSQL-Modelle
- **Abschnittsgrenze ignoriert:** Enthält Teil von Document Store UND Wide-Column
- **Keine Metadaten:** LLM kann keinen Kontext herstellen
- **Wortanzahl-basiert:** Offensichtlich nach fester Länge geschnitten statt nach Semantik

---

## 4. Datenmodell

### 4.1 Pflichtfelder für jeden Chunk

Das Chunk-Schema folgt den Anforderungen der Portfolioprüfung und den Best Practices aus Modul 6:

| Feld | Typ | Zweck | Notwendigkeit |
|------|-----|-------|---------------|
| `chunk_id` | String (UUID) | Eindeutiger Identifikator für jeden Chunk | Der Vector Store liefert nur IDs zurück - ohne `chunk_id` ist der Originaltext nicht auffindbar |
| `chunk_text` | String | Der eigentliche Chunk-Inhalt | Wird dem LLM präsentiert; entspricht dem Embedding-Vektor |
| `document_id` | String (UUID) | Referenz auf das Ursprungsdokument | Ermöglicht Zuordnung mehrerer Chunks zu einem Dokument; wichtig für Kontextherstellung |
| `chunk_index` | Integer | Positionsnummer im Dokument (0-basiert) | Ermöglicht Laden von Nachbar-Chunks; rekonstruiert Reihenfolge für LLM-Kontext |

### 4.2 Vollständiges Schema (Implementierung)

```python
@dataclasses.dataclass
class DocumentChunk(object):
    chunk_id: str                       # Eindeutiger Identifikator (UUID als String)
    document_id: str                    # Eindeutiger Identifikator des Dokumentes (UUID als String)
    chunk_index: int                    # Position im Dokument (0, 1, 2, ...)
    chunk_text: str                     # Der eigentliche Text
    token_count: int                    # Anzahl Tokens für Budgetierung (Entspricht der Zeichenanzahl)
    character_count: int                # Zeichenanzahl
    metadata: DocumentChunkMetadata     # Erweiterte Metadaten

@dataclasses.dataclass  
class DocumentChunkMetadata(object):
    heading: str                        # section_title (Abschnittsüberschrift)
    section: str                        # Abschnittsnummer entspricht heading
    page_number: int                    # Seitennummer (falls relevant)
    source_file: str                    # Name der Quelldatei
    language: str                       # Sprache des Chunks
```

### 4.3 Begründung der Pflichtfelder

#### chunk_id - Warum notwendig?
- Jeder Chunk muss **einzeln adressierbar** sein
- Der Vector Store liefert bei der Suche nur IDs zurück
- Ohne `chunk_id` könnte der Originaltext nicht gefunden werden
- Viele Chunks stammen aus demselben Dokument → eigener Schlüssel erforderlich

#### text - Warum notwendig?
- Der Embedding-Vektor entspricht diesem Text
- Das System muss den Text zurückgeben können
- Für Präsentation und Antwortgenerierung unverzichtbar

#### doc_id - Warum notwendig?
- Mehrere Chunks einem Dokument zuordnen
- Kontext im Prompt herstellen („stammt aus Kapitel XY")
- Dokumentversionen unterscheiden (bei Updates)

#### chunk_num - Warum notwendig?
- Viele Antworten benötigen **mehrere aufeinanderfolgende Chunks**
- Nachbar-Chunks (vorher/nachher) können geladen werden
- Reihenfolge im Prompt rekonstruierbar
- **Ohne chunk_num keine zusammenhängenden Textstellen wiederherstellbar**

#### section_title - Warum notwendig?
- Gibt LLM zusätzliches Verständnis („Text gehört zur ACID-Section")
- Erhöht Retrieval-Qualität (Prompt bekommt mehr Orientierung)
- Hilft bei Strukturierung und Suche
- **Reduziert Halluzinationen und erhöht Präzision** [Portfolioprüfung, Abschnitt 4]

### 4.4 Optionale Felder (implementiert)

| Feld | Typ | Zweck |
|------|-----|-------|
| `token_count` | Integer | Ermöglicht Token-Budgetierung für LLM-Kontext |
| `language` | String | Mehrsprachige Dokumente unterscheiden |
| `source_file` | String | Quelldatei für Debugging und Nachvollziehbarkeit |

---

## 5. Speicherarchitektur

### 5.1 Architekturentscheidung: Polyglot Persistence

Das System implementiert eine **zweischichtige Datenbankarchitektur**, die unterschiedliche Workloads auf spezialisierte Datenbanken verteilt:

| Komponente | Datenbank | Begründung |
|------------|-----------|------------|
| **Chunks (Text + Embeddings)** | MongoDB Atlas | Dokumentorientiert, flexible Metadaten, `$vectorSearch` für Cosinus ANN |
| **Szenarien + Fragen** | PostgreSQL + pgvector | Relationale Struktur, hochperformante Vektorsuche mit HNSW |

Diese Architektur folgt dem Prinzip der **Workload-Isolation**: Chunk-Lookups (I/O-intensiv) und Vektor-Suche (CPU-intensiv) werden auf unterschiedliche Systeme verteilt.

### 5.2 MongoDB: Chunk-Speicher

**Verwendung:** Speicherung aller Document-Chunks mit eingebetteten Embeddings.

```python
# Verbindungsaufbau (database/mongo.py)
mongo_client = pymongo.MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&appName=mongosh")
db = mongo_client["rag"]
chunks_collection = db["chunks"]
```

**Begründung:**
1. **Flexibles Schema:** Unterschiedliche Chunk-Typen (MD, JSON, CSV) haben theoretisch verschiedene Metadaten
2. **Dokumentorientiert:** Ein Chunk ist ein natürliches Dokument mit verschachtelten Metadaten
3. **MongoDB Atlas Vector Search:** Ermöglicht `$vectorSearch`-Aggregation direkt auf der Collection

**Vektorsuche-Implementation:**
```python
# ragutil/chunks_search.py
pipeline = [
    {
        "$vectorSearch": {
            "index": "vec_idx",
            "path": "embedding",
            "queryVector": vector_list,
            "numCandidates": 100,
            "limit": number_of_chunks
        }
    }
]
chunks = list(collection.aggregate(pipeline))
```

### 5.3 PostgreSQL + pgvector: Szenario-Speicher

**Verwendung:** Speicherung von Szenarien und Szenario-Fragen mit deren Embeddings.

```python
# Verbindungsaufbau (database/postgres.py)
connection = psycopg2.connect(
    database="rag",
    host=POSTGRES_HOST,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    port="5432"
)
```

**Datenmodell:**
```sql
-- Szenarien (thematische Kategorien)
CREATE TABLE scenarios (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    embedding VECTOR(384)  -- pgvector-Erweiterung
);

-- Szenario-Fragen (vordefinierte Abfragen pro Szenario)
CREATE TABLE scenario_questions (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(id),
    question TEXT NOT NULL,
    answer TEXT,
    embedding VECTOR(384)
);
```

**Begründung für PostgreSQL:**
1. **pgvector:** Spezialisierte Vektordatenbank-Erweiterung
2. **Relationale Struktur:** Szenarien haben 1:n-Beziehung zu Fragen
3. **Multi-Keyword-Suche:** Effiziente Aggregation mehrerer Keyword-Embeddings

**Vektorsuche für Szenario-Matching:**
```python
# ragutil/scenario_search.py
similarity_filter = " + ".join(["1 - (embedding <-> %s)" for _ in keywords])
cursor.execute(f"""
    SELECT id, name, description, ({similarity_filter}) AS similarity
    FROM scenarios
    ORDER BY similarity DESC
    LIMIT {number_of_scenarios}
""", tuple(keyword_vectors))
```

### 5.4 Architektur-Diagramm

```
┌─────────────────────────────────────────────────────────────────┐
│                      SPEICHERARCHITEKTUR                        │
└─────────────────────────────────────────────────────────────────┘

     ┌───────────────────────┐        ┌───────────────────────┐
     │      PostgreSQL       │        │        MongoDB        │
     │      + pgvector       │        │    (Atlas Vector)     │
     └───────────┬───────────┘        └───────────┬───────────┘
                 │                                │
         ┌───────┴───────┐               ┌────────┴────────┐
         │   scenarios   │               │     chunks      │
         │ (id, name,    │               │ (chunk_id,      │
         │  embedding)   │               │  chunk_text,    │
         └───────┬───────┘               │  embedding,     │
                 │                       │  metadata)      │
         ┌───────┴───────┐               └─────────────────┘
         │ scenario_     │
         │ questions     │
         │ (question,    │
         │  answer,      │
         │  embedding)   │
         └───────────────┘
```

### 5.5 Trade-offs und Begründung

| Aspekt | Entscheidung | Alternative | Begründung |
|--------|--------------|-------------|------------|
| **Chunk-Embeddings** | In MongoDB | Separater Vector Store | Vereinfachte Architektur, atomare Updates |
| **Szenario-Embeddings** | In PostgreSQL | MongoDB | Relationale Beziehungen, Multi-Keyword-Aggregation |
| **Index-Typ** | MongoDB `$vectorSearch` | HNSW in pgvector | MongoDB für Prototyp ausreichend |

**Bewusst in Kauf genommene Trade-offs:**
- MongoDB Vector Search ist langsamer als pgvector HNSW (gemessen: ~10ms vs. ~51ms P95)
- Für Produktion wäre eine Trennung in dedizierte Vector Stores empfohlen

---

## 6. Retrieval-Flow

### 6.1 Architektur: Szenario-basiertes Retrieval

Das System implementiert einen **mehrstufigen Retrieval-Prozess**, der nicht direkt von der Frage zu Chunks geht, sondern über eine Zwischenschicht von **Szenarien** arbeitet. Dies erhöht die thematische Kohärenz der Ergebnisse.

```
┌─────────────────────────────────────────────────────────────────┐
│              SZENARIO-BASIERTER RETRIEVAL-FLOW                  │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │  User-Frage  │
                         │  (String)    │
                         └──────┬───────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 1. KEYWORD-EXTRAKTION (Perplexity)   │
                 │    - LLM extrahiert max. 10 Keywords │
                 │    - Output: JSON-Array              │
                 │    - z.B. ["Index", "B-Baum",        │
                 │            "Performance", "SQL"]     │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 2. SZENARIO-MATCHING (pgvector)      │
                 │    - Keywords → Embeddings           │
                 │    - Multi-Vektor-Suche in scenarios │
                 │    - Aggregierte Similarity-Score    │
                 │    - Top-2 passende Szenarien        │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 3. FRAGEN-RETRIEVAL (PostgreSQL)     │
                 │    - Lade scenario_questions         │
                 │    - Pro Szenario: alle Fragen       │
                 │    - Fragen haben vorberechnete      │
                 │      Embeddings                      │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 4. CHUNK-RETRIEVAL (MongoDB)         │
                 │    - Pro Frage: $vectorSearch        │
                 │    - Top-2 Chunks pro Frage          │
                 │    - Deduplizierung über Szenarien   │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 5. KONTEXT-AUFBAU                    │
                 │    - Chunks nach Szenario gruppieren │
                 │    - Heading + Text kombinieren      │
                 │    - Prompt-Template befüllen        │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 6. ANTWORT-GENERIERUNG (Perplexity)  │
                 │    - System-Prompt: DB-Experte       │
                 │    - Kontext = Szenario-Chunks       │
                 │    - Antwort in Markdown             │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   Antwort    │
                         │   (HTML)     │
                         └──────────────┘
```

### 6.2 Implementierungsdetails

#### Schritt 1: Keyword-Extraktion (LLM)

```python
    # rag.py - extract_keywords()
    prompt = f"""
    Folgendes ist ein User Promt, dieser Soll auf ALLE möglichen Stichworte die auf dessen Szenario zutreffen, runtergrebrochen werden.
    MAXIMAL aber 10 Stichworte. In der AUSGABE von DIR, sollen NUR diese Stichworte rauskommen, KEINERLEI ERKLÄRUNG oder sonstiges.
    Diese Stichworte bitte als JSON-Parsable Array. Sonst keinen Text!

    {user_input}
    """
    response = perplexity_client.prompt(prompt)
    keywords = json.loads(response)  # z.B. ["Indexierung", "B-Baum", "Performance"]
```

**Begründung:** Keywords ermöglichen ein breiteres Szenario-Matching als die direkte Frage. Eine Frage wie "Wie mache ich meine Suche schneller?" erzeugt Keywords wie `["Index", "Performance", "Optimierung", "Cache"]`.

#### Schritt 2: Szenario-Matching (pgvector)

```python
# ragutil/scenario_search.py - match_keywords()
for keyword in keywords:
    embedding = util.embedding.build_embedding(keyword)
    vector = pgvector.psycopg2.vector.Vector(embedding.tolist())
    keyword_vectors.append(vector)

# Multi-Vektor-Similarity: Summe der (1 - Distanz) für alle Keywords
similarity_filter = " + ".join(["1 - (embedding <-> %s)" for _ in keywords])

cursor.execute(f"""
    SELECT id, name, description, ({similarity_filter}) AS similarity
    FROM scenarios
    ORDER BY similarity DESC
    LIMIT 2
""", tuple(keyword_vectors))
```

**Begründung:** Durch Aggregation mehrerer Keyword-Embeddings werden Szenarien gefunden, die zu **allen** relevanten Konzepten passen, nicht nur zum dominantesten.

#### Schritt 3: Fragen-Retrieval (PostgreSQL)

```python
# util/scenario.py - Scenario.get_scenario_questions()
raw_questions = database.postgres.fetch_all(
    "SELECT * FROM scenario_questions WHERE scenario_id = %s",
    "rag",
    (self.id,)
)
return [ScenarioQuestion.from_dict(q) for q in raw_questions]
```

**Begründung:** Jedes Szenario hat vordefinierte Fragen mit vorberechneten Embeddings. Diese dienen als "Brücke" zwischen abstrakten Szenarien und konkreten Chunks.

#### Schritt 4: Chunk-Retrieval (MongoDB $vectorSearch)

```python
# ragutil/chunks_search.py - retrieve_chunks_for_scenario_question()
pipeline = [
    {
        "$vectorSearch": {
            "index": "vec_idx",
            "path": "embedding",
            "queryVector": scenario_question.embedding,
            "numCandidates": 100,
            "limit": 2  # Top-2 pro Frage
        }
    }
]
raw_chunks = list(collection.aggregate(pipeline))
```

**Begründung:** MongoDB Atlas Vector Search nutzt einen vordefinierten Index (`vec_idx`) für effiziente ANN-Suche. `numCandidates: 100` balanciert Recall vs. Latenz.

#### Schritt 5: Kontext-Aufbau

```python
# rag.py - build_question_block()
def build_question_block(question, chunks):
    blocks = [question.question]
    for chunk in chunks:
        chunk_block = f"{chunk.metadata.heading}: {chunk.chunk_text}"
        blocks.append(chunk_block)
    return "\n".join(blocks)
```

**Begründung:** Jeder Chunk wird mit seiner Überschrift präfixiert, damit das LLM den thematischen Kontext versteht.

#### Schritt 6: Antwort-Generierung (Perplexity)

```python
    # rag.py - process_final_results()
    prompt = f"""
    DER USER PROMT:
    {user_input}

    VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
    DEIN SINN DER EXISTENZ:


    Du bist ein DATENBANKEN ENGINEER Experte.
    Deine Aufgabe ist es, eine optimierte Datenbanksystem für ein neues Projekt zu entwerfen.
    Berücksichtige dabei die folgenden Anforderungen:
    - Halte dich an die Anforderungen des User Promts
    - Die Informationen die du über die Kontext Scenarien bekommst sind dein DATENGRUNDLAGEN GOTT. Dies ist deine volle Wissensquelle.
    - Es gibt keinerlei Möglichkeit auf Rückfragen, weshalb du alleine mit den dir gegebenen Informationen arbeiten musst.
    - Evaluiere die besten Technologien und Architekturen, die den Anforderungen am besten entsprechen. NUTZE dein WISSEN aus den SCENARIO KONTEXT. 2 Möglichkeiten MAXIMAL!
    - Erstelle ein detailliertes Datenbankschema, das die Struktur und Beziehungen der Daten klar definiert.
    - Berücksichtige Skalierbarkeit, Leistung und Sicherheit in deinem Design. Solange sie den ANFORDERUNGEN des USER PROMTS entsprechen.
    - Gib eine Begründung für deine Designentscheidungen, Annahmen, Berechnungen und die gewählten Technologien.
    DU BEARBEITEST DIE AUFGABE IN DEUTSCHER SPRACHE, ABER ENGLISCHE TECHNISCHE BEGRIFFE SIND ERLAUBT.
    DU ANTWORTEST NUR AUF DEN USER INPUT DES USERS, DER REST IST NUR DEINE WISSENSGRUNDLAGE. NICHTS AUF DAS DU ANTWORTEN SOLLST, ODER DARFST!
    Deine Antwort darf KEINERLEI Links oder Verweise auf externe Quellen enthalten!
    Nutze bitte MARKDOWN Formatierung in deiner Antwort und Volksmundverständliche Sprache mit benötigten Fachbegriffen.
    NIEMALS JavaScript Code oder HTML code in der Antwort nutzen!

    VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
    DEINE WISSENSDATENBANK:

    {query_part}
    """
    response = perplexity_client.prompt(prompt)
    return marko.convert(response)  # Markdown → HTML
```

**Begründung:** Das LLM erhält strenge Anweisungen, sich auf die bereitgestellten Chunks zu stützen und keine externen Quellen zu zitieren. Die Antwort wird via `marko` in HTML konvertiert.

### 6.3 Performance-Charakteristik

| Schritt | Datenbank/API | Typische Latenz | Kommentar |
|---------|---------------|-----------------|-----------|
| Keyword-Extraktion | Perplexity API | ~5s | Netzwerk-Round-Trip |
| Szenario-Matching | PostgreSQL/pgvector | ~300ms | Multi-Vektor-Aggregation |
| Chunk-Retrieval | MongoDB $vectorSearch | ~450ms pro Frage | Abhängig von numCandidates |
| Antwort-Generierung | Perplexity API | ~30s | Token-Generation |
| **Gesamt** | - | **~35-40s meistens** | Dominated by LLM-Calls |

---

## 7. Tests & Beispiele

### 7.1 Beispiel-Frage (Startup-Szenario)

**Kontext:** Ein Startup-Gründer plant einen Online-Shop und möchte verstehen, wie die Datenbank schnelle Produktsuchen ermöglicht.

**Eingabe:** „Welche Datenbank-Indexierung brauche ich für schnelle Produktsuchen in meinem Online-Shop?"

### 7.2 Top-3 gefundene Chunks

#### Chunk 1 (Similarity: 0.89)

| Feld | Wert |
|------|------|
| `chunk_id` | `idx_001` |
| `section_title` | „B-Baum-Indizes" |
| `source_file` | `db_indexing_query_processing.md` |
| `chunk_text` | „B-Bäume sind balancierte Suchbäume mit folgenden Eigenschaften: Alle Blätter liegen auf derselben Höhe. Jeder Knoten enthält eine sortierte Menge von Schlüsseln und Kindzeigern. Suchen, Einfügen und Löschen laufen in O(log n). Vorteile: Sehr gut für Bereichsanfragen (>, <, BETWEEN) und für ORDER BY geeignet." |

**Relevanz für Startup:** Erklärt, warum B-Baum-Indizes für Preisfilter („Produkte unter 50€") und sortierte Produktlisten ideal sind.

#### Chunk 2 (Similarity: 0.84)

| Feld | Wert |
|------|------|
| `chunk_id` | `idx_002` |
| `section_title` | „Hash-Indizes" |
| `source_file` | `db_indexing_query_processing.md` |
| `chunk_text` | „Hash-Indizes verwenden eine Hash-Funktion, um einen Suchschlüssel direkt auf einen Bucket abzubilden. Eigenschaften: Sehr schnell für exakte Gleichheitsabfragen (=). Nicht geeignet für Bereichsanfragen oder ORDER BY." |

**Relevanz für Startup:** Zeigt, dass Hash-Indizes für exakte Produktsuchen (SKU, Artikelnummer) geeignet sind, aber nicht für Preisfilter.

#### Chunk 3 (Similarity: 0.71)

| Feld | Wert |
|------|------|
| `chunk_id` | `idx_003` |
| `section_title` | „Grundlagen der Indexierung" |
| `source_file` | `db_indexing_query_processing.md` |
| `chunk_text` | „Ein Index ist eine zusätzliche Datenstruktur, die den Zugriff auf Zeilen einer Tabelle beschleunigt, indem sie Suchattribute sortiert speichert. RDBMS setzen standardmäßig häufig B-Baum-Varianten (B+ Bäume) ein." |

**Relevanz für Startup:** Liefert Grundlagenwissen, das der Gründer für die Gespräche mit Entwicklern braucht.

### 7.3 Chunking-Strategie-Vergleich (aus Testlauf)

Ein dedizierter Chunking-Test verglich drei Strategien anhand der Frage: *„Was mache ich wenn ich einen Netzwerk Timeout habe?"*

| Strategie | Chunk-Size | Overlap | Top-1 Treffer | Section-Metadaten |
|-----------|------------|---------|---------------|-------------------|
| **Naive** | 150 Zeichen | 0 | `...Netzwerk-Timeout Bei Timeouts...` | N/A |
| **Rekursiv** | 300 Zeichen | 60 | `### 2.2 Netzwerk-Timeout...` | N/A |
| **Heading-Aware** | Dynamisch | 0 | `Bei Timeouts erhöhen Sie...` | `2. Fehlerbehebung` |

**Ergebnis:** Die Heading-Aware-Strategie liefert als einzige korrekte `section`-Metadaten, was die Retrieval-Qualität und LLM-Kontextgebung verbessert.

**Begründung der Wahl:** 
- Naive Chunks zerreißen semantische Einheiten ("SZI-Sekretariat-Problem")
- Rekursive Chunks verbessern Overlap, aber keine Metadaten
- Heading-Aware nutzt natürliche Dokumentstruktur

### 7.4 Metriken und Evaluation

#### Verwendete Metriken

| Metrik | Definition | Unser Wert |
|--------|------------|------------|
| **Precision@K** | Anteil relevanter Chunks unter Top-K | 3/3 = **100%** |
| **Mean Reciprocal Rank (MRR)** | 1/Position des ersten relevanten Chunks | 1/1 = **1.0** |
| **Latenz (P95)** | 95. Perzentil der Antwortzeit | ~60ms (Vector Search) |

#### Performance-Messungen (aus Testlauf 13.12.2025)

| Operation | Ops/s | P95 Latenz | SLO-Status |
|-----------|-------|------------|------------|
| MongoDB Single find_one | 1.011 | 1.47ms | Erfüllt |
| MongoDB Batch find ($in) | 8.985 | 0.16ms | Erfüllt |
| MongoDB Vector Search | 0 | 10.138ms | Nicht erfüllt |
| pgvector ANN (HNSW) | 19 | 60.07ms | Knapp verfehlt |

#### Analyse der Ergebnisse

**Stärken:**
1. **Hohe Precision:** Alle Top-3 Chunks sind relevant für die Beispielfrage
2. **Semantische Kohärenz:** Chunks aus demselben Dokument mit aufsteigender `chunk_num` ermöglichen Kontextrekonstruktion
3. **Metadaten-Nutzung:** `section_title` erlaubt dem LLM, die Chunk-Zugehörigkeit zu verstehen

**Schwächen:**
1. **MongoDB Vector Search zu langsam:** Mit 10.138ms P95 ist das 50ms-SLO deutlich verfehlt
2. **Kein Pre-Filtering:** Ohne Metadaten-Filter wird der gesamte Vektorraum durchsucht
3. **Keine Workload-Isolation:** Vector Search und Chunk-Lookup konkurrieren um Ressourcen

**Ursachenanalyse:**
- MongoDB ist nicht für hochperformante Vektorsuche optimiert
- Fehlende Indexierung in MongoDB (nur lineare Suche)
- Gemäß Modul 7: „B-Trees können die 50ms Latenz bei ANN-Suche niemals einhalten"

---

## 8. Reflexion

### 8.1 Verbesserungspotenzial bei mehr Zeit

#### Technische Verbesserungen

| Bereich | Aktuelle Lösung | Verbesserung | Begründung |
|---------|-----------------|--------------|------------|
| **Chunk-Embeddings** | MongoDB $vectorSearch | pgvector mit HNSW | Spezialisierte Vektor-Indizes bieten bessere Latenz |
| **LLM-Calls** | 2x Perplexity (Keywords + Antwort) | Lokales Modell für Keywords | Reduziert Latenz um ~800ms pro Anfrage |
| **Szenario-Anzahl** | Statisch Top-2 | Dynamisch nach Similarity-Threshold | Vermeidet irrelevante Szenarien bei spezifischen Fragen |
| **Caching** | Keines | Redis für häufige Szenario-Matches | Reduziert DB-Last bei wiederkehrenden Themen |

#### Architektonische Verbesserungen

1. **Vollständige Workload-Isolation:**
   - Chunk-Embeddings in pgvector statt MongoDB
   - MongoDB nur für Text-Lookups (I/O-optimiert)
   - Separater Index-Server für ANN-Suche

2. **Pre-Filtering implementieren:**
   - Metadaten-basierte Vorfilterung vor Vektorsuche
   - Reduziert Suchraum und verbessert Precision

3. **Feedback-Loop:**
   - Logging welche Chunks in Antworten verwendet werden
   - Iterative Verbesserung der Szenario-Definitionen

### 8.2 Kritische Designentscheidungen

#### Entscheidung 1: Szenario-basiertes Retrieval statt direktem Chunk-Matching

**Auswirkung:** Positiv  
**Begründung:** Die Zwischenschicht "Szenarien" ermöglicht thematisch kohärente Ergebnisse. Statt nur die ähnlichsten Chunks zu finden, werden Chunks im Kontext eines passenden Szenarios ausgewählt. Dies verhindert, dass semantisch ähnliche aber thematisch unpassende Chunks in die Antwort einfließen.

#### Entscheidung 2: Polyglot Persistence (MongoDB + PostgreSQL)

**Auswirkung:** Positiv  
**Begründung:** Die Trennung von Chunk-Speicherung (MongoDB) und Szenario-Matching (PostgreSQL/pgvector) nutzt die Stärken beider Systeme:
- MongoDB: Flexible Metadaten, schnelle Dokument-Lookups
- PostgreSQL: Relationale Szenario-Fragen-Beziehungen, optimierte Vektorsuche

#### Entscheidung 3: Heading-Aware Chunking (nur ##)

**Auswirkung:** Positiv  
**Begründung:** Der Chunking-Test zeigte, dass Heading-Aware-Chunking als einzige Strategie korrekte Section-Metadaten liefert. Die Entscheidung, nur `##` (H2) zu verwenden, verhindert zu fragmentierte Chunks bei tiefer Verschachtelung.

#### Entscheidung 4: Perplexity für Keyword-Extraktion

**Auswirkung:** Gemischt  
**Begründung:** Ermöglicht intelligente Keyword-Erweiterung (Synonyme, verwandte Begriffe), aber fügt ~800ms Latenz hinzu. Für einen Prototyp akzeptabel, für Produktion wäre ein lokales Modell oder Regel-basierte Extraktion schneller.

### 8.3 Lessons Learned

1. **Chunking ist Datenmodellierung, nicht Textschneiden**
   - Die Chunk-Grenzen (##) bestimmen maßgeblich die Retrieval-Qualität
   - Metadaten (heading, source_file) sind für LLM-Kontext oft wichtiger als der Text selbst

2. **Szenario-Abstraktion verbessert Kohärenz**
   - Direkte Frage→Chunk-Suche liefert oft thematisch gemischte Ergebnisse
   - Die Zwischenschicht "Szenarien" gruppiert verwandte Chunks

3. **Messen vor Optimieren**
   - Der Chunking-Vergleich zeigte klare Unterschiede zwischen Strategien
   - Performance-Tests identifizierten MongoDB Vector Search als Bottleneck

4. **Polyglot Persistence ist kein Overhead**
   - Unterschiedliche Workloads profitieren von spezialisierten Datenbanken
   - Die Komplexität ist beherrschbar durch klare Schnittstellen

### 8.4 Fazit

Das System erfüllt die Anforderungen der Portfolioprüfung:
- Dokumente laden und chunken (Heading-Aware für MD, Key-Value für JSON, Batching für CSV)
- Embeddings erzeugen (all-MiniLM-L6-v2)
- Speicherung in NoSQL (MongoDB) + Vektor-DB (pgvector)
- Retrieval-Flow mit Vektorsuche
- Antwort-Generierung mit LLM (Perplexity)

Die Szenario-basierte Architektur geht über den Minimal-Scope hinaus und demonstriert, wie thematische Kohärenz durch eine zusätzliche Abstraktionsebene erreicht werden kann.

---

## Anhang: Technische Referenzen

### Verwendete Technologien

| Komponente | Technologie | Version |
|------------|-------------|---------|
| Embedding-Modell | sentence-transformers (all-MiniLM-L6-v2) | 2.x |
| Chunk-Speicher | MongoDB (Atlas Vector Search) | 7.x |
| Szenario-Speicher | PostgreSQL + pgvector | 16.x |
| Chunking-Library | langchain-text-splitters | 0.x |
| LLM-API | Perplexity (Sonar) | - |
| Markdown-Rendering | marko | - |
| Backend | Python/Flask | 3.12 |

### Datenbank-Schemas

**MongoDB Collection: `rag.chunks`**
```json
{
  "_id": ObjectId,
  "chunk_id": "uuid",
  "document_id": "uuid",
  "chunk_index": 0,
  "chunk_text": "...",
  "token_count": 150,
  "character_count": 800,
  "embedding": [0.1, 0.2, ...],  // 384 floats
  "metadata": {
    "heading": "Abschnittstitel",
    "section": "2",
    "page_number": 0,
    "source_file": "file.md",
    "language": "de"
  }
}
```

**PostgreSQL Tables:**
```sql
-- rag.scenarios
CREATE TABLE scenarios (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    embedding VECTOR(384)
);

-- rag.scenario_questions
CREATE TABLE scenario_questions (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(id),
    question TEXT NOT NULL,
    answer TEXT,
    embedding VECTOR(384)
);
```

---

*Der Datenbank Design Deputy - Ein RAG-System für Startups und KMU*  
*Dokument erstellt im Rahmen der DHBW Portfolioprüfung, Dezember 2025*
