# Chunking-Strategie für RAG-System

## Übersicht
Das RAG-System nutzt ein mehrstufiges Chunking-Konzept, um große Dokumente für die Einbettung (Embedding) und Suche optimal zu zerlegen. Diese Dokumentation beschreibt die Chunking-Logik, Größen und die Integration in die Datenbank-Layer.

## 1. Chunking-Konzept

### Definition
**Chunking** ist der Prozess, Eingabedokumente in kleinere, semantisch sinnvolle Teile (Chunks) zu unterteilen. Jeder Chunk wird separat embeddet und gespeichert, um eine granulare Suche und Kontextretrieval zu ermöglichen.

### Gründe für Chunking
- **Embedding-Limits**: Sprachmodelle haben Kontext-Fenster (z. B. 8K Tokens). Ein Chunk passt in diese Limits.
- **Retrieval-Genauigkeit**: Kleinere, fokussierte Chunks erhöhen die Chance, relevante Passage zu finden.
- **Speichereffizienz**: Viele kleine Embeddings sind besser zu indizieren als wenige sehr große.
- **Fehlertoleranz**: Ausfälle bei einzelnen Chunks beeinflussen nicht das ganze Dokument.

---

## 2. Chunking-Parameter

| Parameter | Wert | Beschreibung |
|-----------|------|-------------|
| **Chunk-Größe** | 512 Tokens (~2000 Zeichen) | Standard-Größe für die meisten Inhalte |
| **Chunk-Overlap** | 50 Tokens (~200 Zeichen) | Überlappung zwischen aufeinanderfolgenden Chunks, um Kontextverlust zu vermeiden |
| **Separator** | Satz + Absatz | Hierarchisch: zuerst nach Absätzen, dann nach Sätzen chunken |
| **Min. Chunk-Größe** | 100 Tokens (~400 Zeichen) | Chunks unterhalb dieser Größe werden nicht separat gespeichert (zu wenig Kontext) |

### Rationale
- **512 Tokens**: Ein guter Kompromiss zwischen Kontexttiefe (Absätze bleiben zusammenhängend) und Granularität.
- **50 Tokens Overlap**: Erhöht Retrieval-Qualität, ohne Speicher massiv zu belasten (~10% Overhead).
- **Hierarchische Separator**: Sätze sind natürliche semantische Einheiten; Absätze strukturieren thematisch.

---

## 3. Chunking-Prozess

```

1. Rohdokument einlesen (PDF, TXT, Markdown, etc.)
↓
2. Vorverarbeitung: Whitespace normalisieren, Header extrahieren
↓
3. Hierarchisches Chunking:
a) Nach Absätzen (\n\n) aufteilen
b) Große Absätze nach Sätzen teilen (Satzgrenzen-Erkennung)
c) Sätze zu Chunks von ~512 Tokens kombinieren
↓
4. Overlap hinzufügen: Letzte 50 Tokens des vorherigen Chunks
an den Anfang des nächsten Chunks prependen
↓
5. Metadaten pro Chunk:
    - chunk_id (eindeutig)
    - document_id (Referenz zum Original)
    - chunk_index (0-basiert, Position im Dokument)
    - chunk_text (der eigentliche Text)
    - token_count (Anzahl Tokens)
    - metadata: {heading, section, page_number, ...}
↓
6. Embedding generieren für chunk_text
↓
7. Chunk + Embedding in DB speichern (PostgreSQL/MongoDB)
```

---

## 4. Implementierungsort

Die Chunking-Logik befindet sich in:

**Hauptort:**
- `backend/services/document_ingestion.py` (oder ähnlich)
  - Funktion: `chunk_document(text: str, max_tokens: int = 512, overlap_tokens: int = 50) -> List[Dict]`
  - Abhängigkeiten: tiktoken (für Token-Counting), spaCy oder nltk (für Satzgrenzen)

**Aufruf-Pipeline:**
1. `backend/api/upload_endpoint.py`: Empfängt Dokument-Upload
2. `backend/services/document_ingestion.py`: Chunking + Embedding
3. `backend/db/postgres_layer.py` / `backend/db/mongo_layer.py`: Speichern in DB

---

## 5. Beispiel-Chunk-Struktur

```

{
"chunk_id": "doc_123_chunk_0",
"document_id": "doc_123",
"chunk_index": 0,
"chunk_text": "Dies ist der erste Chunk. Er enthält mehrere Sätze und ca. 512 Tokens. Overlap-Text vom vorherigen Chunk…",
"token_count": 512,
"character_count": 2048,
"metadata": {
"heading": "Einleitung",
"section": "1.0",
"page_number": 1,
"source_file": "document.pdf",
"language": "de"
},
"embedding": [0.123, -0.456, 0.789, ...],
"created_at": "2025-11-28T09:40:00Z"
}

```

---

## 6. Best Practices

- **Chunk-Größe anpassen**: Für sehr technische Docs ggf. 256 Tokens; für Erzähltext 512–768 Tokens.
- **Sprache beachten**: Deutsche Texte mit Umlauten und Komposita korrekt tokenisieren (mit `tiktoken` oder spaCy-de).
- **Metadaten reichhaltig**: Speichere Überschriften, Seitennummern, Quelldatei – hilft bei Re-Ranking.
- **Overlap für RAG kritisch**: Zu wenig Overlap → Kontextverlust an Chunk-Grenzen; zu viel → Speicherverschwendung.
- **Versioning**: Bei Änderungen der Chunking-Strategie alte Embeddings invalidieren und neu embedden.

---

## 7. Performance und Skalierung

| Szenario | Chunk-Größe | Overlap | Begründung |
|----------|-------------|---------|-----------|
| Web-Artikel (2–5 KB) | 512 Tokens | 50 Tokens | Schnelle Einbettung, gute Retrieval |
| Lehrbuch (100+ Seiten) | 512 Tokens | 50 Tokens | Standard; bei Bedarf 256 für dichte Inhalte |
| Chat-Historie | 128 Tokens | 0 Tokens | Schneller, da viele kleine Messages |
| Code-Dokumentation | 256 Tokens | 25 Tokens | Weniger Overlap, da Code strukturiert ist |

---

## 8. Monitoring & Debugging

Überwache diese Metriken:
- **Durchschnittliche Chunks pro Dokument**: Sollte linear mit Doc-Größe wachsen.
- **Token-Verschwendung durch Overlap**: Sollte ~10% sein.
- **Embedding-Latenz pro Chunk**: Ziel: < 100 ms für 512 Tokens.
- **Chunk-Hitrate in Retrieval**: % der Top-K Chunks, die relevant sind für Query.

---
