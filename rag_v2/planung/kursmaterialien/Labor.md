Chunking-Strategien & Retrieval Tuning (3–5 Minuten)
Titel: „Warum euer RAG-System steht und fällt mit guten Chunks“
1. Einstieg
Viele Leute denken:

„Chunking ist trivial — einfach alle X Wörter schneiden.“

Das ist das klassische Anfängerloch.
Über 50 % der Retrieval-Fehler entstehen durch schlechtes Chunking.

2. Warum Chunking überhaupt notwendig ist
LLMs können nur begrenzte Kontextfenster lesen.
Daher müssen große Dokumente in kleine Teile (Chunks) zerlegt werden:

200–500 Tokens pro Chunk

mit Overlap von 20–30 %

Das Ziel: Jeder Chunk enthält eine kohärente semantische Einheit.

3. Schlechte Chunking-Strategien (Beispiele)
❌ „Snippet every 500 characters“
→ bricht Sätze, Tabellen, Abschnitte auf
→ Embeddings werden inhaltlich wertlos

❌ „Einfach immer 200 Tokens“
→ trennt Rezepte, Tabellen, Definitionen mitten durch
→ Künstliche Brüche, semantisch falsch

4. Gute Chunking-Strategien
A) Absatz-basiertes Chunking
Chunks entsprechen Textabschnitten.
Semantisch sauber, Retrieval hat hohe Precision.

B) Heading-aware Chunking
Überschriften definieren Logik:

Installation
Fehlerbehebung
Garantiebedingungen
Chunks enthalten je einen vollständigen Abschnitt.

C) Semantisches Chunking
Z. B. mit Transformers / Sentence Embedding-Scores.
Wird in der Industrie → Standard.

5. Chunk Overlap (warum es wichtig ist)
Overlap von 15–30 % löst:

Satzabbrüche

verlorene Kontextwörter

„vergessene“ Schlussfolgerungen

Ohne Overlap verpasst die ANN-Suche oft die relevanten Teile → schlechte Recall@K.

6. Retrieval Tuning — was ANN wirklich braucht
Parameter, die entscheiden:
K (Top-K)

ef_search (HNSW)

Indexgröße (HNSW M)

Normalisierung (z. B. für Cosine)

Praktische Faustregeln:

K = 8–12 → meistens ideal

ef_search = 20–50 (Qualität vs. Latenz)

Keine Cosine-Suche ohne Normalisierung

Keine L2-Suche mit unnormalisierten Embeddings

7. Kleines Experiment für heute (Labor)
Testet:

Chunk-Größe 150 vs 300 vs 500 Tokens

Overlap 0 % vs 20 %

K = 5 vs K = 10 vs K = 20

Mit/ohne Überschriften-Basiertes Chunking

→ Schaut euch an:

Precision (wie viele Treffer sind wirklich relevant?)

Recall (wie viele relevante Chunks fehlen?)

Latenz

Erwartetes Ergebnis:
Chunkgröße & Overlap erzeugen deutlich mehr Wirkung als Vektor-Modelle oder Indexparameter.


„Chunks allein sind wertlos.“
Warum jeder Chunk eine sichere Rückverbindung braucht**

Kurz, klar, wichtig:

Ein Chunk ist nur ein Stück Text.
Ohne Kontext ist er bedeutungslos.
Eure wichtigste Aufgabe ist nicht das Chunking selbst,
sondern die Modellierung der Beziehungen.

Was jeder Chunk in einem RAG-System immer haben muss:

chunk_id – Primärschlüssel

text – der eigentliche Ausschnitt

embedding – Vektor

doc_id – Verweis auf das Ursprungsdokument

abschnitt_id / section_title – semantischer Kontext

produkt → version → dokumenttyp – Metadaten

position („chunk_number“) im Dokument – Reihenfolge

👉 Ohne diese Beziehungen ist ein RAG-System nicht baubar.

Fazit:
Vektorsuche liefert nur den Schlüssel zu den wichtigen Chunks.
Der Prompt braucht:

den Text

den Namen des Dokuments

die Version

evtl. mehrere aufeinanderfolgende Chunks

und manchmal die Überschrift oder umliegenden Kontext

Die drei realistischsten Speicherstrategien (mit Entscheidungskriterien)
Strategie A: Alles-in-Postgres
Tabelle: chunks

| chunk_id | doc_id | text | embedding | metadata_jsonb | chunk_num |

Vorteile:

einfaches JOIN

starke Konsistenz

sauberer Filter

weniger Moving Parts

ideal zum Lernen

Nachteile:

nicht super performant für Millionen von Chunks

BLOB-Handling mäßig

Wann gut?
👉 RAG mit < 500.000 Chunks
👉 Uni-Projekte
👉 Systeme, die starke Filter brauchen

Strategie B: pgvector für Embeddings + MongoDB für Text & Metadaten
Vorteile:

Mongo = perfekter Document Store für semistrukturierte Infos

pgvector = starker ANN-Index

extrem große Datenmengen skalierbar

saubere Trennung: Text hier, Vektor dort

Nachteile:

Cross-DB-Queries brauchen Applikationslogik

etwas komplexer

Wann gut?
👉 Reale Enterprise-Workloads
👉 Viele Dokumentarten (PDF, HTML, Logs, Tabellen)

Strategie C: Vectorindex + Filestore + Metadata-DB
z. B.:

Vektoren in pgvector

Text in S3 / MinIO

Metadaten in Postgres/Mongo

doc_id referenziert die Files

Vorteile:

Skalierbar

Billiger Storage für große PDFs

Ideal für mehrsprachige & große Dokus

Nachteile:

Aufwendiger zu implementieren

Wann gut?
👉 Massive Dokumente (>100 MB)
👉 Große Enterprises (ServiceNow, Salesforce etc.)

Wo Chunks schiefgehen (und was das für eure Speicherung bedeutet)


1. „Ich speichere nur die Embeddings.“
→ Ergebnis: Du bekommst chunk_ids, aber du weißt nicht:

aus welchem Dokument

in welchem Kontext

welche Version

welcher Abschnitt
→ völlig unbrauchbar für Prompts.

2. „Ich speichere Text, aber nicht chunk_num.“
→ Du kannst keine zusammenhängenden Chunks laden.

3. „Ich speichere Text ohne Überschrift / section_title.“
→ LLM hat keinen Kontext → höhere Halluzinationsrate.

4. „Ich speichere Dokumentversionen nicht.“
→ Du mixst v1.0 und v3.2 und erzeugst Falschaussagen.

5. „Ich speichere Metadaten nicht sauber.“
→ Filtering klappt nicht → RAG wird unpräzise.

„Baut drei Varianten einer Chunk-Datenbank und vergleicht die Qualität“
Ziel:
wollen sehen dass
Speicherstrategie = Retrievalqualität beeinflusst.

🟣 Schritt 1 — Drei Speichermodelle implementieren
A) Minimales Modell (schlecht)
Nur:

chunk_id

embedding

text

→ kein doc_id, keine Metadaten

B) Besseres Modell (gut)
chunk_id

embedding

text

doc_id

chunk_num

section_title

C) Best-Practice Modell (exzellent)
chunk_id

embedding

text

doc_id

chunk_num

section_title

product_family

version

visibility

document_type

created_at

Schritt 2 — Sucht dieselbe Frage in allen drei Modellen
Beispiel:

„Warum blinkt die Kaffeemaschine gelb?“

Messt:

Relevanz der Top-3 Chunks

Vollständigkeit der Information

Kontextqualität

Prompt-Länge

Zeit bis zur Finalantwort

Schritt 3 — Bewertet nach Punkten
Kriterium	Minimal	Gut	Exzellent
Relevanz	2/10	6/10	9/10
Kontext	1/10	6/10	10/10
LLM-Qualität	3/10	7/10	10/10
Filtering	0/10	5/10	10/10
Geschwindigkeit	irrelevant	relevant	sehr gut
Schritt 4 — Diskussion
Frage:
„Was hättet ihr beim Modell A niemals rekonstruieren können?“

Erwartete Einsichten:

Dokumentkontext fehlt

Reihenfolge fehlt

Metadaten fehlen

Prompt wird schlecht

RAG hat „falsche Erinnerung“

Fazit :
Chunking ist nicht das Schneiden von Text,
Chunking ist das Modellieren von Beziehungen zwischen Fragmenten und dem Gesamtdokument.

Ein guter Chunk ist nicht nur Text + Embedding,
sondern ein eingebetteter Datenknoten in einem sauberen Datenmodell.


Hinweis:
Metadaten beim INGEST (Dokument → Metadaten)
Frage: „Wie bekommt jedes Dokument seine Metadaten?“

Antwort:
→ Deterministisch. Immer. Ohne LLM.

Warum?

Das Dokument gehört zu Produkt X (steht im Dateipfad).

Das Dokument ist Modell KA-22 (steht im Titel, SKU-Katalog).

Dokumenttyp ist Troubleshooting (kommt aus Ordnerstruktur).

Version kommt aus Datenbank oder YAML-Header.

Beispiele aus echten Systemen:

/products/coffee/ka-22/troubleshooting_v2024.pdf

„Kaffeemaschine KA-22 Bedienungsanleitung“

Diese Infos sind objektiv bekannt, nicht zu erraten.

Deshalb:

„Man nutzt NICHT das LLM, um zu erraten, ob ein Chunk zu Kaffeemaschine gehört.“

Denn: Die Maschine „weiß“ schon vorher, dass ein Chunk zur Kaffeemaschine gehört, weil das in den Metadaten des Dokuments steht.

2. Metadaten beim Retrieval: Filter auf die USER-FRAGE anwenden (Query → Filter)
Frage: „Wie finde ich heraus, welche Metadatenfilter auf die Frage des Nutzers angewendet werden sollen?“

User fragt:

„Warum blinkt meine Kaffeemaschine gelb?“

Jetzt muss das System entscheiden:

Produktfamilie → Kaffeemaschine

Dokumenttyp → Troubleshooting

Sprache → de

Rolle → customer

Modell → vielleicht KA-22 (wenn explizit genannt)

Diese Informationen stehen NICHT in den Dokumenten, sondern müssen aus der Userfrage extrahiert werden.

Und dafür nutzt man i. d. R. ein LLM oder klassisches ML.

Zusammenfassung:
Dokumente → Metadaten = deterministisch, kein LLM

User-Frage → Filter = Klassifikation, oft mit LLM