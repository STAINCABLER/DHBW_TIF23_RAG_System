# MODUL 6 -- Chunking ist Datenmodellierung, nicht Textschneiden

Nach diesem Modul kannst du:

- Chunking als Modellierungsentscheidung verstehen und nicht als „technischen Schritt".
- Chunks so gestalten, dass sie zu deinen Access Paths passen.
- Chunks so strukturieren, dass die Retrieval-Qualität steigt und der kritische Pfad kurz bleibt.
- Chunk-Metadaten so definieren, dass Queries planbar, reproduzierbar und performant werden.
- typische Fehler beim Chunking vermeiden (Überlappung, zu große Chunks, falscher Kontext).

## 1. Warum Chunking Datenmodellierung ist

Viele glauben:

„Chunking ist: Alle 300 Wörter schneiden."

Das ist falsch. (denke einmal an das SZI-Sekretariat-Öffnungszeiten-Beispiel)

Chunking ist eine Datenmodellierungsentscheidung, die bestimmt:

- wie dein System Informationen sucht
- wie Daten im Speicher organisiert sind
- wie Retrieval funktioniert
- wie schnell die DB arbeitet
- wie viel Kontext ein LLM bekommt
- wie konsistent die Antworten sind

Chunking entscheidet direkt über den Access Path und die gesamte Datenbankstruktur.

## 2. Chunking folgt immer dem Access Path

Der Access Path bestimmt die Chunk-Regeln. Beispiele:

- „LLM braucht funktionale Abschnitte" → Chunk = Abschnitt
- „Support will gezielt nach Unterkapitel filtern" → Chunk = Unterkapitel
- „Daten sind zeitbasiert" → Chunk = Events / Fenster
- „Große Handbücher werden seitenweise gebraucht" → Chunk = Seite
- „Risikoanalysen brauchen stabile Semantik" → Chunk = semantisch dichte Einheiten

Chunking folgt nie der Wortanzahl.
Chunking folgt immer dem Retrieval-Verhalten.

## 3. Die vier Modellierungs-Entscheidungen des Chunkings

Jedes Chunk-Modell basiert auf vier Entscheidungen:

### 3.1 Entscheidung 1 — Chunk-Grenzen (Was ist eine Einheit?)

Optionen:

- Abschnitt
- Unterkapitel
- Funktionsblock
- Tabelle
- Liste
- logische Operation
- zeitliche Einheit
- semantische Einheit

Eine gute Chunk-Grenze ist:

- stabil (ändert sich nicht ständig)
- semantisch kohärent
- retrieval-relevant
- wiederauffindbar über Metadaten

### 3.2 Entscheidung 2 — Chunk-Größe (Small vs Medium vs Large)

Richtlinien:

**Small Chunks (50–150 Wörter)** — ideal für hochpräzise Antworten (Support, Fachfragen)

**Medium Chunks (150–300 Wörter)** — gut für erklärende Fragen mit Kontext

**Large Chunks (300–800 Wörter)** — gut, wenn Zusammenhänge nicht fragmentierbar sind (z. B. lange Codebeispiele)

Chunk-Größe ist eine Qualitäts- und Performance-Entscheidung.
Kleinere Chunks = bessere Retrieval-Präzision.
Größere Chunks = weniger Fragmentierung, stabilerer Kontext.

### 3.3 Entscheidung 3 — Überlappung (Overlap: ja/nein)

Overlap ist nur sinnvoll, wenn:

- Information nicht genau an Abschnittsgrenzen steht
- das LLM zweistufige Abhängigkeiten braucht
- du irreführende Chunks vermeiden willst

Empfehlung:

- 0–10% Overlap für klassisches RAG
- 20–30% für narrativen Text
- 0% für technische Doku mit klaren Abschnitten

### 3.4 Entscheidung 4 — Metadaten (explizit und retrieval-relevant)

Gute Chunk-Metadaten erhöhen Retrieval-Genauigkeit stärker als Embeddings.

**Essentielle Metadaten:** chunk_id, doc_id, section_title, position, keywords, version, product_family (z. B. für Support)

**Optionale Metadaten:** embedding_id, confidence_score, page_number

## 4. Chunking + Datenbanken: warum das Modell die DB bestimmt

Chunking entscheidet:

- ob du viele kleine Dokumente brauchst (MongoDB)
- ob du einzelne Chunks schnell laden musst (Mongo + Index)
- ob deine Retrieval-Pfade von ANN oder Fulltext abhängen
- wie groß deine Objekte in MongoDB werden dürfen
- wie oft pgvector auf IDs zugreifen muss

Chunking ist damit ein DB-Designschritt.

## 5. Vier vollständige Beispiele

### 5.1 Beispiel: Produktdokumentation (Support-RAG)

**1) Access Path:**

- User stellt Frage
- ANN sucht passende Embeddings → liefert 5–10 chunk_ids
- Mongo lädt die jeweiligen Chunk-Dokumente
- LLM erhält Text + Metadaten

**2) Chunk-Grenzen:** Chunk = Abschnitt (Begründung: Support-Fragen sind meist abschnittsbezogen)

**3) Chunk-Größe:** 150–250 Wörter → ideal für präzise Antworten ohne Kontextverlust

**4) Overlap:** 0–10% → nur wenn Absätze hart getrennt sind

**5) Metadaten (precompute):** section_title, position, product_family, doc_id

**6) Finales Chunk-Dokument:**

```json
{
  "chunk_id": "doc_123_05",
  "doc_id": "doc_123",
  "position": 5,
  "section_title": "Reset Vorgang",
  "text": "...",
  "keywords": ["reset", "error", "start"],
  "product_family": "KA-22",
  "version": "2024",
  "embedding_id": "emb_123_05"
}
```

**7) Warum funktioniert dieses Chunking gut?** Stabile Abschnitte, hohe Retrieval-Präzision, schnelle punktuelle Reads, kleine Dokumente → niedrige Latenz.

### 5.2 Beispiel: Code-Dokumentation

**1) Access Path:**

- LLM sucht erklärende Codeblöcke
- Ziel: vollständige Funktion oder Klasse

**2) Chunk-Grenzen:** Chunk = vollständige Funktion (niemals halbe Funktionen!)

**3) Chunk-Größe:** 150–600 Wörter je nach Funktion → große Chunks explizit erwünscht

**4) Overlap:** 0% — Code ist strukturiert → kein Overlap nötig

**5) Metadaten:** file_path, function_name, language, complexity_score

**Finales Modell:**

```json
{
  "chunk_id": "code_4471",
  "file_path": "src/payment/calc.py",
  "function_name": "compute_fee",
  "language": "python",
  "text": "def compute_fee(...",
  "complexity": 12
}
```

### 5.3 Beispiel: Juristische Dokumente

**Access Path:** „Gib mir das relevante rechtliche Kapitel"

**Chunk-Grenzen:** Chunk = Paragraph (gesetzliche Einheit)

**Chunk-Größe:** 50–200 Wörter

**Overlap:** 0% (Paragraphgrenzen sind fest)

**Metadaten:** paragraph_number, law_name, version

### 5.4 Beispiel: IoT-Konfigurationslog (große Chunks sinnvoll!)

**Access Path:** „Gib mir den kompletten Log-Zustand der letzten 15 Minuten"

**Chunk-Grenzen:** Chunk = Zeitfenster (z. B. 15 min)

**Chunk-Größe:** 500–2000 Wörter → große Chunks sind sinnvoll

**Overlap:** 0% → Logs sind zeitlich geordnet

**Metadaten:** timestamp_start, timestamp_end, device_id, severity_count

## 6. Typische Fehler

**Chunking nach Wortanzahl** — erzeugt instabile und semantisch inkonsistente Chunks

**Zu große Chunks ohne Grund** — Latenz steigt, Präzision sinkt

**Keine Metadaten** — Retrieval wird schwach und nicht filterbar

**Embeddings im Chunk speichern** — Dokument wird zu groß, Updates unhandlich

**Abschnittsgrenzen ignorieren** — LLM sieht Fragmente ohne Kontext

## 7. Mini-Übung (10 Minuten)

Gegeben: 1 Seite Betriebsanleitung

Aufgabe:

1. Definiere die Chunk-Grenze
2. Entscheide Chunk-Größe
3. Entscheide Overlap
4. Definiere die Metadaten
5. Gib ein JSON-Schema für einen Chunk an

Abgabe: 1 JSON-Beispiel + 3 Sätze Begründung
