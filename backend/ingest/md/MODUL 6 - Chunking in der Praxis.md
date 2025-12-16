# MODUL 6 — Chunking in der Praxis

## 0. Ziel dieses Moduls

Nach diesem Modul kannst Du:

- ✔ verschiedene Dokumentquellen sicher einlesen (PDF, Webseiten, Office)
- ✔ Texte kontrolliert in sinnvolle Chunks zerlegen
- ✔ Chunk-Größe, Overlap und Metadaten bewusst wählen
- ✔ verstehen, warum Chunking Teil der Datenmodellierung ist
- ✔ dein Chunking an den Retrieval-Pfad anpassen (kritischer Pfad aus Modul 4)

## 1. Warum Chunking wichtig ist

Chunking bestimmt:

- wie gut dein RAG Inhalte findet
- wie viel Kontext pro Chunk ins LLM passt
- wie viele Embeddings entstehen (Kosten!)
- wie schnell deine Retrieval-Pfade laufen
- welche Metadaten dein System braucht

**Wichtig:**
Chunking ist kein „Text-Schneiden".
Chunking ist eine Modellierungsentscheidung, die dein späteres Datenmodell prägt.

## 2. Pflicht-Werkzeuge für sauberes Chunking

Diese drei Werkzeuge reichen für jedes Capstone-Projekt.

### 2.1 Unstructured.io – robustes Einlesen schwieriger Dokumente

**Wofür:** PDFs, Scans, Office-Dateien, Bilder, E-Mails, Webseiten.

**Warum:**

- erkennt Absätze, Überschriften und Tabellen
- liefert „Elemente" statt Roh-Text
- ideal für Support-Dokumentation & Manuals

**Code:**

```python
from unstructured.partition.pdf import partition_pdf

elements = partition_pdf("manual.pdf")
for e in elements:
    print(e.category, e.text[:80])
```

### 2.2 LangChain Loader – einheitliche Schnittstelle für alle Formate

**Wofür:** PDF, HTML, Markdown, Word, Text.

**Warum:**

- sehr einfache API
- Loader erzeugen Dokumentobjekte mit Metadaten
- ideal für Projekte mit vielen Quellen

**Code:**

```python
from langchain.document_loaders import PyPDFLoader

loader = PyPDFLoader("manual.pdf")
docs = loader.load()
```

### 2.3 LangChain RecursiveCharacterTextSplitter – kontrolliertes Chunking

**Wofür:** Chunking basierend auf Absätzen, Sätzen, Wörtern.

**Warum:**

- Standard für RAG
- klare Kontrolle über Größe + Overlap
- verhindert harte Schnitte mitten im Satz

**Code:**

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
)

chunks = splitter.split_documents(docs)
```

## 3. Optional: professionelle Tools für strukturierte oder semantische Chunks

Diese Tools brauchst Du nicht zwingend für das Capstone, aber sie zeigen dir, wie professionelle Systeme arbeiten.

### 3.1 LlamaIndex NodeParser – Chunking mit vollständiger Kontrolle

**Wofür:** Dokumente mit klarer Struktur, hierarchische Inhalte.

**Warum:**

- erzeugt Nodes mit Metadaten
- ideal für Manuals, Kapitel, Unterkapitel
- funktioniert gut in Kombination mit Embeddings

**Code:**

```python
from llama_index.core.node_parser import SimpleNodeParser

parser = SimpleNodeParser.from_defaults(chunk_size=300, chunk_overlap=50)
nodes = parser.get_nodes_from_documents(docs)
```

### 3.2 LangChain SemanticChunker – thematische Chunk-Grenzen

**Wofür:** Chunking anhand semantischer Übergänge.

**Warum:**

- erkennt Themenwechsel automatisch
- ideal für lange Tutorials, FAQs, Chat-Protokolle
- nutzt Embeddings um „natürliche Breakpoints" zu finden

**Code:**

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain.embeddings import OpenAIEmbeddings

chunker = SemanticChunker(OpenAIEmbeddings())
chunks = chunker.create_documents([text])
```

### 3.3 Whisper / FasterWhisper – Audio zu Chunk-Text

**Wofür:** Meeting-Mitschnitte, Hotline-Gespräche, Support-Calls.

**Warum:**

- stabilste Speech-to-Text Engine
- liefert Text + Zeitstempel
- ideal für „temporal chunking"

**Code:**

```python
from faster_whisper import WhisperModel

model = WhisperModel("medium")
segments, info = model.transcribe("call.wav")

text = "\n".join(seg.text for seg in segments)
```

## 4. Chunking-Strategien, die Du im Capstone verwenden sollst

### 4.1 Chunk-Größe und Overlap

- chunk_size 200–400
- overlap 20–60
- je größer das Dokument, desto kleiner der Overlap
- je mehr Kontext das LLM braucht, desto größer der Overlap

### 4.2 Chunk-Metadaten (Pflicht!)

Jeder Chunk sollte mindestens enthalten:

| Feld | Warum |
|------|-------|
| doc_id | Quelle des Chunks |
| chunk_id | eindeutige ID |
| position | Reihenfolge im Dokument |
| section_title | für Retrieval |
| keywords | optional |
| source_type | (pdf, html, audio, etc.) |

### 4.3 Chunking immer am Retrieval-Flow ausrichten

Frage dich:

- Welche Query Paths (Modul 4) holen Chunks ab?
- Wie viele Reads pro Request?
- Wie wichtig ist die Latenz?
- Brauche ich Abschnitts-Metadaten?
- Braucht mein Anwendungsfall semantische Chunks?

Genau diese Antworten bestimmen dein Chunking.

## 5. Mini-Aufgabe (10–20 Minuten)

**A) Lade ein PDF ein (z. B. ein öffentliches Produktmanual).**

Verwende:

- Unstructured
- RecursiveCharacterTextSplitter

Erzeuge:

- 20–50 Chunks
- mit Overlap
- inkl. section_title (falls vorhanden)

**B) Ergänze folgende Pflicht-Metadaten pro Chunk:**

doc_id, chunk_id, position, section_title, source_type

**C) Überprüfe deine Chunking-Qualität:**

- Sind Abschnitte logisch?
- Gibt es harte Schnitte?
- Ist die Chunk-Größe konsistent?
- Fehlen Metadaten?

## 6. Check-dein-Verständnis

Kannst Du:

- ✔ erklären, warum Chunking Teil der Datenmodellierung ist?
- ✔ PDFs, Webseiten und Office-Dokumente einlesen?
- ✔ Chunkgrößen + Overlap sinnvoll wählen?
- ✔ Metadaten für Retrieval erzeugen?
- ✔ Chunking an Query Paths aus Modul 4 ausrichten?

Wenn ja → Modul 6 bestanden.

## 7. LLM-Assist (optional)

Beispiel-Prompts:

- „Bitte zeige mir, ob meine Chunk-Metadaten vollständig sind."
- „Welche Probleme erkennst Du in dieser Chunk-Struktur?"
- „Welche Chunk-Größe würde für mein Retrieval funktionieren?"
