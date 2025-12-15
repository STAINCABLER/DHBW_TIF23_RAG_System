# Portfolio: Datenbank Design Assistant

**Projekt:** DHBW TIF23 RAG-System  
**Datum:** Dezember 2025  
**Thema:** Retrieval-Augmented Generation für Datenbankberatung bei Startups und KMU

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

### 1.1 Zielsetzung: Der Datenbank Design Assistant

Das entwickelte RAG-System – der **„Datenbank Design Assistant"** – dient als intelligenter Beratungsassistent für **Startups und kleine lokale Unternehmen (KMU)**, die ihre IT-Infrastruktur erstmalig aufbauen oder erweitern möchten. Diese Zielgruppe verfügt häufig über begrenzte Ressourcen und fehlendes Fachwissen im Bereich Datenbankarchitektur, benötigt aber dennoch fundierte Entscheidungsgrundlagen.

**Primäres Ziel:**
- Unterstützung von Gründern und technischen Leitern bei der Auswahl und Gestaltung einer passenden Datenbankarchitektur
- Bereitstellung von Best Practices und Entscheidungshilfen durch semantische Suche in kuratierten Fachmaterialien
- Demokratisierung von Datenbankwissen: Komplexe Konzepte verständlich für Nicht-Experten aufbereiten

### 1.2 Zielgruppe und deren Herausforderungen

| Zielgruppe | Typische Herausforderung | Wie der Assistant hilft |
|------------|--------------------------|-------------------------|
| **Tech-Startups** | Schnelle Skalierung, unklare Anforderungen | Empfehlungen zu skalierbaren NoSQL-Lösungen |
| **Lokale Einzelhändler** | Kundendaten, Inventar, wenig IT-Budget | Einfache, kosteneffiziente Datenbankmodelle |
| **Handwerksbetriebe** | Auftragsverwaltung, Terminplanung | Relationale Grundlagen und Normalisierung |
| **Freiberufler/Agenturen** | Projektdaten, Kundenverwaltung | Flexible Schema-Optionen (Document Stores) |

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

### 1.4 Warum RAG für diesen Use Case?

Startups und KMU haben spezifische Anforderungen, die ein RAG-System ideal adressiert:

1. **Kontextbezogene Antworten:** Statt generischer Ratschläge liefert das System Empfehlungen basierend auf kuratierten Fachtexten
2. **Aktualität:** Die Wissensbasis kann ohne Modell-Neutraining aktualisiert werden
3. **Nachvollziehbarkeit:** Quellenangaben ermöglichen Verifizierung der Empfehlungen
4. **Domänenfokus:** Spezialisierung auf Datenbankthemen statt allgemeinem Weltwissen

**Begründung:** Diese Fragetypen entsprechen realen Entscheidungssituationen bei Infrastrukturaufbau und erfordern semantisches Verständnis statt exakter Keyword-Matches. Gemäß Modul 6 der Kursmaterialien folgt das Chunking-Design dem Access Path: „LLM braucht funktionale Abschnitte" → Chunk = Abschnitt [vgl. Modul 6, Abschnitt 2].

---

## 2. Dokumentenauswahl + Datenbasis

### 2.1 Verwendete Dokumente

Die Datenbasis besteht aus **eigenen Zusammenfassungen und Lehrtexten** zu Datenbankthemen. Folgende Dokumentkategorien wurden verwendet:

| Dokument | Format | Thema | Quelle |
|----------|--------|-------|--------|
| `db_nosql_models_overview.md` | Markdown | NoSQL-Datenmodelle (Key-Value, Document, Wide-Column, Graph) | Eigene Zusammenfassung |
| `db_indexing_query_processing.md` | Markdown | B-Baum-Indizes, Hash-Indizes, Anfrageoptimierung | Eigene Zusammenfassung |
| `db_transactions_acid_isolation.txt` | Text | ACID-Eigenschaften, Isolation Levels | Vorlesungsmitschriften |
| `db_normalization_anomalies.txt` | Text | Normalformen, Anomalien | Vorlesungsmitschriften |
| `db_sql_qa_pairs.json` | JSON | Q&A-Paare zu SQL-Grundlagen | Strukturierte Lernkarten |
| `db_isolation_levels_matrix.csv` | CSV | Isolation-Level-Matrix | Tabellarische Zusammenfassung |

### 2.2 Auswahlkriterien

Die Dokumentenauswahl folgt den Prinzipien aus dem Kursmaterial:

1. **Semantische Kohärenz:** Jedes Dokument behandelt ein abgeschlossenes Themengebiet
2. **Keine KI-generierten Texte:** Ausschließlich eigene Zusammenfassungen und Vorlesungsinhalte
3. **Strukturierte Abschnitte:** Markdown-Überschriften ermöglichen heading-aware Chunking
4. **Variabilität der Formate:** CSV, JSON, Markdown und Text decken verschiedene Chunking-Strategien ab

**Wichtig:** Im Gegensatz zum „SZI-Sekretariat-Beispiel" aus dem Kursmaterial, bei dem unstrukturierte Fließtexte problematisch sind, nutzen wir explizit strukturierte Dokumente mit klaren Abschnittsgrenzen. Dies erhöht die Retrieval-Qualität signifikant [vgl. Modul 6, Abschnitt 3.1].

---

## 3. Chunking-Design

### 3.1 Chunking-Strategie

Das System verwendet **Heading-Aware Chunking** basierend auf Markdown-Überschriften. Diese Strategie folgt der Erkenntnis aus Modul 6: „Chunking folgt nie der Wortanzahl. Chunking folgt immer dem Retrieval-Verhalten."

**Implementierung (md_chunker.py):**
```python
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
markdown_splitter = langchain_text_splitters.MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)
```

### 3.2 Chunk-Größe

| Parameter | Wert | Begründung |
|-----------|------|------------|
| **Ziel-Chunk-Größe** | 150–300 Wörter | Optimal für erklärende Fragen mit Kontext [Modul 6, Abschnitt 3.2] |
| **Minimum** | 50 Wörter | Vermeidet semantisch leere Chunks |
| **Maximum** | 500 Wörter | Verhindert Kontextverlust bei komplexen Erklärungen |

**Begründung:** Gemäß den Kursmaterialien sind Medium Chunks (150–300 Wörter) „gut für erklärende Fragen mit Kontext". Da unser Use Case primär Konzepterklärungen umfasst, ist diese Größe ideal.

### 3.3 Overlap

| Parameter | Wert | Begründung |
|-----------|------|------------|
| **Overlap** | **0%** | Markdown-Abschnitte haben klare semantische Grenzen |

**Begründung:** Die Kursmaterialien empfehlen „0% für technische Doku mit klaren Abschnitten" [Modul 6, Abschnitt 3.3]. Da unsere Dokumente durch Überschriften klar strukturiert sind, ist kein Overlap notwendig. Overlap wäre nur sinnvoll bei narrativen Texten, wo Information „nicht genau an Abschnittsgrenzen steht".

### 3.4 Anzahl der Chunks

| Dokumenttyp | Anzahl Dokumente | Chunks pro Dokument (Ø) | Gesamt-Chunks |
|-------------|------------------|-------------------------|---------------|
| Markdown | 6 | ~8 | ~48 |
| JSON | 3 | ~12 | ~36 |
| CSV | 3 | ~5 | ~15 |
| Text | 5 | ~6 | ~30 |
| **Gesamt** | **17** | - | **~129** |

### 3.5 Beispiel: Guter vs. Schlechter Chunk

#### ✅ Guter Chunk

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

#### ❌ Schlechter Chunk

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
| `chunk_id` | String (UUID) | Eindeutiger Identifikator für jeden Chunk | Der Vector Store liefert nur IDs zurück – ohne `chunk_id` ist der Originaltext nicht auffindbar |
| `text` | String | Der eigentliche Chunk-Inhalt | Wird dem LLM präsentiert; entspricht dem Embedding-Vektor |
| `doc_id` | String (UUID) | Referenz auf das Ursprungsdokument | Ermöglicht Zuordnung mehrerer Chunks zu einem Dokument; wichtig für Kontextherstellung |
| `chunk_num` | Integer | Positionsnummer im Dokument (0-basiert) | Ermöglicht Laden von Nachbar-Chunks; rekonstruiert Reihenfolge für LLM-Kontext |
| `section_title` | String | Abschnittsüberschrift | Erhöht Retrieval-Qualität; reduziert Halluzinationen [Modul 6, Abschnitt 3.4] |

### 4.2 Vollständiges Schema (Implementierung)

```python
@dataclasses.dataclass
class DocumentChunk(object):
    chunk_id: str           # Eindeutiger Identifikator (UUID)
    document_id: str        # Referenz auf Ursprungsdokument
    chunk_index: int        # Position im Dokument (0, 1, 2, ...)
    chunk_text: str         # Der eigentliche Text
    token_count: int        # Anzahl Tokens für Budgetierung
    character_count: int    # Zeichenanzahl
    metadata: DocumentChunkMetadata  # Erweiterte Metadaten

@dataclasses.dataclass  
class DocumentChunkMetadata(object):
    heading: str            # section_title (Abschnittsüberschrift)
    section: str            # Abschnittsnummer
    page_number: int        # Seitennummer (falls relevant)
    source_file: str        # Quelldatei
    language: str           # Sprache des Chunks
```

### 4.3 Begründung der Pflichtfelder

#### chunk_id – Warum notwendig?
- Jeder Chunk muss **einzeln adressierbar** sein
- Der Vector Store liefert bei der Suche nur IDs zurück
- Ohne `chunk_id` könnte der Originaltext nicht gefunden werden
- Viele Chunks stammen aus demselben Dokument → eigener Schlüssel erforderlich

#### text – Warum notwendig?
- Der Embedding-Vektor entspricht diesem Text
- Das System muss den Text zurückgeben können
- Für Präsentation und Antwortgenerierung unverzichtbar

#### doc_id – Warum notwendig?
- Mehrere Chunks einem Dokument zuordnen
- Kontext im Prompt herstellen („stammt aus Kapitel XY")
- Dokumentversionen unterscheiden (bei Updates)

#### chunk_num – Warum notwendig?
- Viele Antworten benötigen **mehrere aufeinanderfolgende Chunks**
- Nachbar-Chunks (vorher/nachher) können geladen werden
- Reihenfolge im Prompt rekonstruierbar
- **Ohne chunk_num keine zusammenhängenden Textstellen wiederherstellbar**

#### section_title – Warum notwendig?
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

### 5.1 Architekturentscheidung

| Komponente | Datenbank | Begründung |
|------------|-----------|------------|
| **Chunks (Text + Metadaten)** | MongoDB | Dokumentorientiert, flexibles Schema, schnelle Lookups |
| **Embeddings (Vektoren)** | MongoDB (im Chunk-Dokument) | Vereinfachte Architektur, ausreichend für Prototyp |
| **Szenarien** | PostgreSQL | Relationale Struktur für Szenario-Fragen-Beziehungen |

### 5.2 Begründung: Warum MongoDB für Chunks?

1. **Flexibles Schema (Schema-on-Read):** Unterschiedliche Chunk-Typen (MD, JSON, CSV) können verschiedene Metadaten haben, ohne Schema-Migration
2. **Dokumentorientiert:** Ein Chunk ist ein natürliches Dokument mit verschachtelten Metadaten
3. **Aggregation Pipeline:** Ermöglicht komplexe Vektor-Ähnlichkeitssuche direkt in der Datenbank
4. **Schnelle Single-Document-Lookups:** Nach Retrieval müssen einzelne Chunks per `chunk_id` schnell geladen werden (gemessen: 1.011 Ops/s für `find_one`, P95: 1.47ms)

**Referenz Kursmaterial:** „Chunking entscheidet, ob du viele kleine Dokumente brauchst (MongoDB), ob du einzelne Chunks schnell laden musst (Mongo + Index)" [Modul 6, Abschnitt 4]

### 5.3 Begründung: Embedding-Speicherort

**Entscheidung:** Embeddings werden **im Chunk-Dokument selbst** in MongoDB gespeichert (Feld `embedding`).

**Begründung:**
- **Vereinfachte Architektur:** Kein separater Vector Store notwendig
- **Atomare Operationen:** Chunk und Embedding werden gemeinsam geschrieben
- **Prototyp-geeignet:** Für ~129 Chunks ist MongoDB Vector Search ausreichend
- **Konsistenz:** Keine Referenz-Logik zwischen zwei Systemen notwendig

**Trade-off (bewusst in Kauf genommen):**
- MongoDB Vector Search ist langsamer als spezialisierte Lösungen (gemessen: 9.516 ms Mean vs. 51 ms bei pgvector HNSW)
- Für Produktion wäre Workload-Isolation mit dediziertem Vector Store (pgvector) empfohlen [Modul 7]

### 5.4 Alternative Architektur (nicht implementiert, aber analysiert)

Gemäß Modul 7 und 8 wäre für Produktion folgende Architektur optimal:

| Workload | Datenbank | Latenz-Budget |
|----------|-----------|---------------|
| ANN-Suche | pgvector (PostgreSQL) | ≤50ms P95 |
| Chunk-Lookup | MongoDB | ≤60ms P95 |
| Sessions/Cache | Redis | ≤5ms P95 |

**Warum nicht implementiert:** Der Prototyp-Scope erlaubt explizit keine komplexen Multi-DB-Architekturen [Portfolioprüfung, Abschnitt 3].

---

## 6. Retrieval-Flow

### 6.1 Ablaufdiagramm

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAG RETRIEVAL PIPELINE                       │
└─────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │  User-Frage  │
                         │  (String)    │
                         └──────┬───────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 1. KEYWORD-EXTRAKTION (LLM)          │
                 │    - Perplexity API extrahiert       │
                 │      relevante Keywords              │
                 │    - Output: ["Index", "B-Baum",     │
                 │               "Performance"]         │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 2. SZENARIO-MATCHING                 │
                 │    - Keywords → Embedding            │
                 │    - Vektor-Suche in Szenarien       │
                 │    - Top-2 passende Szenarien        │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 3. CHUNK-RETRIEVAL                   │
                 │    - Pro Szenario: Fragen-Embeddings │
                 │    - Cosine Similarity in MongoDB    │
                 │    - Top-5 Chunks pro Frage          │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 4. CHUNK-LADEN                       │
                 │    - chunk_ids → MongoDB find()      │
                 │    - Metadaten + Text laden          │
                 │    - Deduplizierung                  │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 5. KONTEXT-ZUSAMMENFÜHRUNG           │
                 │    - Chunks nach Relevanz sortieren  │
                 │    - section_title als Kontext       │
                 │    - Prompt-Template befüllen        │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────────────────┐
                 │ 6. ANTWORT-GENERIERUNG (LLM)         │
                 │    - Perplexity API                  │
                 │    - Kontext + Frage → Antwort       │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   Antwort    │
                         │   (String)   │
                         └──────────────┘
```

### 6.2 Implementierungsdetails

#### Schritt 1: Frage → Embedding

```python
# Embedding-Modell: all-MiniLM-L6-v2 (384 Dimensionen)
model = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
embedding = model.encode(user_question)
```

**Begründung Modellwahl:**
- **Schnell:** Kleine Modellgröße (22M Parameter)
- **Mehrsprachig:** Unterstützt Deutsch und Englisch
- **384 Dimensionen:** Guter Kompromiss zwischen Qualität und Speicher

#### Schritt 2: Vektor-Search → relevante Chunks

```python
pipeline = [
    {
        "$addFields": {
            "similarity": {
                "$reduce": {
                    "input": {"$range": [0, 384]},
                    "initialValue": 0,
                    "in": {
                        "$add": ["$$value", {
                            "$multiply": [
                                {"$arrayElemAt": ["$embedding", "$$this"]},
                                {"$arrayElemAt": [query_vector, "$$this"]}
                            ]
                        }]
                    }
                }
            }
        }
    },
    {"$sort": {"similarity": -1}},
    {"$limit": 5}
]
```

#### Schritt 3-4: Laden der Original-Chunks

```python
chunk = DocumentChunk.load_from_id(chunk_id)
# Lädt: chunk_text, metadata.heading, document_id, chunk_index
```

#### Schritt 5: Zusammenführen

Die Chunks werden mit ihren Metadaten zu einem Prompt-Kontext zusammengeführt:

```python
question_block = f"""
Abschnitt: {chunk.metadata.heading}
Quelle: {chunk.metadata.source_file}
---
{chunk.chunk_text}
"""
```

#### Schritt 6: Antwort erzeugen

```python
result = perplexity_client.query(
    context=combined_chunks,
    question=user_input
)
```

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

### 7.3 Metriken und Evaluation

#### Verwendete Metriken

| Metrik | Definition | Unser Wert |
|--------|------------|------------|
| **Precision@K** | Anteil relevanter Chunks unter Top-K | 3/3 = **100%** |
| **Mean Reciprocal Rank (MRR)** | 1/Position des ersten relevanten Chunks | 1/1 = **1.0** |
| **Latenz (P95)** | 95. Perzentil der Antwortzeit | ~60ms (Vector Search) |

#### Performance-Messungen (aus Testlauf 13.12.2025)

| Operation | Ops/s | P95 Latenz | SLO-Status |
|-----------|-------|------------|------------|
| MongoDB Single find_one | 1.011 | 1.47ms | ✅ Erfüllt |
| MongoDB Batch find ($in) | 8.985 | 0.16ms | ✅ Erfüllt |
| MongoDB Vector Search | 0 | 10.138ms | ❌ Nicht erfüllt |
| pgvector ANN (HNSW) | 19 | 60.07ms | ⚠️ Knapp verfehlt |

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
- Fehlende HNSW-Indexierung in MongoDB (nur lineare Suche)
- Gemäß Modul 7: „B-Trees können die 50ms Latenz bei ANN-Suche niemals einhalten"

---

## 8. Reflexion

### 8.1 Verbesserungspotenzial bei mehr Zeit

#### Technische Verbesserungen

| Bereich | Aktuelle Lösung | Verbesserung | Begründung (Kursmaterial) |
|---------|-----------------|--------------|---------------------------|
| **Vector Store** | MongoDB (Aggregation Pipeline) | pgvector mit HNSW-Index | „Spezialisierte Vektor-Indexe opfern Genauigkeit für Geschwindigkeit" [Modul 7] |
| **Workload-Isolation** | Keine | Dedizierte Datenbanken pro Workload | „Widersprüchliche Workloads dürfen sich nicht blockieren" [Modul 8] |
| **Pre-Filtering** | Nicht implementiert | Metadaten-basiertes Filtering vor ANN | „Reduziert CPU-Last drastisch" [Modul 8, Abschnitt 3.2] |
| **Chunk-Größe** | Statisch (heading-aware) | Adaptiv nach Dokumenttyp | „Code-Dokumentation: 150-600 Wörter" [Modul 6, Beispiel 5.2] |

#### Architektonische Verbesserungen

1. **Polyglot Persistence implementieren:**
   - MongoDB für Chunks (I/O-optimiert)
   - pgvector für Embeddings (CPU-optimiert)
   - Redis für Caching (Latenz-optimiert)

2. **HNSW-Tuning durchführen:**
   - Parameter `M` und `ef` optimieren
   - Trade-off Latenz vs. Recall messen
   - Ziel: ≤50ms P95 für ANN-Suche

3. **Metadaten-Extraktion verbessern:**
   - Schwache Metadaten aus Text ableiten (z.B. mit unstructured.io)
   - Keywords automatisch extrahieren
   - Difficulty-Level für Chunks berechnen

### 8.2 Kritische Designentscheidungen

#### Entscheidung 1: Heading-Aware Chunking statt feste Wortanzahl

**Auswirkung:** Positiv  
**Begründung:** Verhindert das „SZI-Sekretariat-Problem", bei dem semantische Einheiten zerrissen werden. Chunks entsprechen natürlichen Abschnittsgrenzen und sind dadurch kohärenter.

#### Entscheidung 2: Embeddings in MongoDB statt separater Vector Store

**Auswirkung:** Negativ für Performance, positiv für Einfachheit  
**Begründung:** Vereinfacht die Architektur erheblich (ein System statt zwei), aber die gemessene Latenz (10.138ms) ist inakzeptabel für Produktion. Für einen Prototyp mit ~129 Chunks akzeptabel.

#### Entscheidung 3: all-MiniLM-L6-v2 als Embedding-Modell

**Auswirkung:** Neutral  
**Begründung:** Schnell und ressourcenschonend, aber möglicherweise weniger präzise als größere Modelle (z.B. text-embedding-ada-002). Für deutschsprachige Fachbegriffe wäre ein mehrsprachig optimiertes Modell wie `paraphrase-multilingual-MiniLM-L12-v2` besser geeignet.

#### Entscheidung 4: Szenario-basiertes Retrieval

**Auswirkung:** Positiv  
**Begründung:** Durch die Zwischenschicht „Szenarien" wird die Suche strukturiert. Statt einer direkten Frage→Chunk-Suche erfolgt: Frage→Szenario→Szenario-Fragen→Chunks. Dies erhöht die thematische Kohärenz der Ergebnisse.

### 8.3 Lessons Learned

1. **Chunking ist Datenmodellierung, nicht Textschneiden** [Modul 6, Titel]
   - Die Chunk-Grenzen bestimmen maßgeblich die Retrieval-Qualität
   - Metadaten sind oft wichtiger als das Embedding selbst

2. **Workload-Isolation ist kein Luxus, sondern Notwendigkeit**
   - Ohne Isolation beeinflussen sich ANN-Suche und Lookups gegenseitig
   - SLOs können nur mit dedizierter Ressourcenzuweisung garantiert werden

3. **Messen vor Optimieren**
   - Die Performance-Tests haben gezeigt, dass MongoDB Vector Search ungeeignet ist
   - Ohne Messungen wäre diese Erkenntnis nicht möglich gewesen

4. **Zielgruppenorientierung zahlt sich aus**
   - Die Fokussierung auf Startups und KMU ermöglicht präzisere Fragetypen
   - Praxisnahe Beispiele (Online-Shop, Kundenverwaltung) verbessern die Retrieval-Qualität

---

## Anhang: Technische Referenzen

### Verwendete Technologien

| Komponente | Technologie | Version |
|------------|-------------|---------|
| Embedding-Modell | sentence-transformers (all-MiniLM-L6-v2) | 2.x |
| Chunk-Speicher | MongoDB | 7.x |
| Chunking-Library | langchain-text-splitters | 0.x |
| LLM-API | Perplexity | - |
| Backend | Python/Flask | 3.12 |

### Quellenverweise (Kursmaterialien)

- **Modul 6:** Chunking ist Datenmodellierung, nicht Textschneiden
- **Modul 7:** Embeddings als Datentyp mit eigenem Workload
- **Modul 8:** Workload-Isolation durch Polyglot Persistence
- **Portfolioprüfung:** Anforderungsspezifikation und Bewertungskriterien

---

*Datenbank Design Assistant – Ein RAG-System für Startups und KMU*  
*Dokument erstellt im Rahmen der DHBW Portfolioprüfung, Dezember 2025*
