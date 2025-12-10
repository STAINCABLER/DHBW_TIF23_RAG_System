1. Ziel des Projekts 
Ihr baut ein kleines, funktionales RAG-System, das Fragen zum Thema „Datenbanken / NoSQL / Indexing / Model & Workload Design“ beantworten kann.
Das System soll keine vollständige KI-App sein, sondern ein Mini-Prototyp, mit dem ihr demonstriert:

wie man Dokumente sinnvoll chunked,

wie man sie in einer NoSQL-Datenbank speichert,

wie man Embeddings erzeugt und speichert,

wie man per Vektorsuche relevante Chunks findet,

wie man die Ergebnisse zusammenführt,

und wie man begründete Architekturentscheidungen trifft.

Das Projekt ist ein NoSQL-/Data-Engineering-Lernprojekt, kein „KI-Projekt“.

Da Ihr hierfür ein LLM und idealerweise ein Embedding-Modell braucht: hier habt Ihr freie Wahl -stellt in der Präsentation halt kurz vor, was Ihr benutzt habt.

2. Endergebnis: Was ihr abgeben müsst
A) Code (kurz & klar, nicht groß)
Ein kleines Skript oder Notebook, das Folgendes demonstriert:

Dokument(e) laden

Chunking anwenden

Embeddings erzeugen

Speicherung:

Dokumente + Chunks in MongoDB (oder z.B. SQLite-JSON - aber bitte mit Begründung warum)

Embeddings in z.B. pgvector

Retrieval Flow für 1 Beispielanfrage (ich werde in der Präsentation auch eine Frage an Euer System stellen)

Ausgabe:

Gefundene Chunks

Optional: eine generierte Kurz-Antwort (kann einfache Heuristik sein)

Wichtig:
Es reicht, wenn das System eine Frage sinnvoll beantwortet. (und ich werde keine "super-komplexen" Fragen stellen)
Es muss nicht robust, hübsch oder komplex sein.

B) Schriftliche Ausarbeitung (max. 6–10 Seiten) – Pflichtteil
Die Ausarbeitung ist vom "Umfang" her der kleinere Teil der Bewertung, ABER enthält quasi DIE wichtig(st)en Teile der Arbeit, die Ihr dann auch in der Präsentation zeigt!


Sie muss folgende Kapitel enthalten:

1. Ziel & Use Case
– Was soll das Mini-RAG können?
– Welche Art Fragen soll es beantworten?

2. Dokumentenauswahl + Datenbasis
Ihr verwendet:
Mindestens 2–3 Lehrtextabschnitte (denkt z.B. an das SZi-Sekreatariat-Beispiel! Welches natürlich für Datenbanken das Gegenteil von "gut", bzw "geeignet" ist) über Datenbanken, z.B.:

eure eigenen Mitschriften

Folieninhalte

Wikipedia-Artikel zu NoSQL, Indexen,...

eigene zusammenfassende Texte

→ keine externen KI-Generierten langen Texte.

3. Chunking-Design
Pflicht:

Wie groß sind eure Chunks? (wieder an SZI-Sekretariat-Beispiel denken)

Welchen Overlap nutzt ihr?

Warum?

Wie viele Chunks entstehen?

Beispiel eines guten und eines schlechten Chunks.

4. Datenmodell
Pflichtfelder für jeden Chunk:

chunk_id

text

doc_id

chunk_num

section_title

wobei
1. chunk_id (eindeutiger Identifikator)
Ein technischer, eindeutiger Schlüssel für jeden Chunk.
Warum notwendig?

Jeder Chunk muss einzeln adressierbar sein.

Der Vector Store liefert nur eine ID zurück – ohne chunk_id könnten wir den Originaltext nicht finden.

Viele Chunks können aus demselben Dokument stammen → brauchen eigenen Schlüssel.

2. text (der eigentliche Chunk-Inhalt)
Der Textausschnitt, der später dem LLM präsentiert wird.
Warum notwendig?

Der Embedding-Vektor entspricht diesem Text.

Das System muss den Text zurückgeben können.

Für die Präsentation und die Antwortgenerierung unverzichtbar.

3. doc_id (Referenz auf das Ursprungsdokument)
Eine eindeutige Kennung für das gesamte Dokument, aus dem der Chunk stammt.
Beispiele:

„index_lecture_01“

„wiki_acid“

„mongodb_basics“

Warum notwendig?

Um mehrere Chunks einem Dokument zuordnen zu können.

Um im Prompt Kontext herzustellen („dieser Chunk stammt aus Kapitel XY“).

Um Dokumentversionen unterscheiden zu können (falls später relevant).

4. chunk_num (Positionsnummer im Dokument)
Eine fortlaufende Nummer (0, 1, 2, 3, ...), die angibt, an welcher Position der Chunk im Ursprungsdokument steht.

Warum notwendig?

Viele Antworten benötigen mehrere aufeinanderfolgende Chunks.

Durch chunk_num kann das System „Nachbar-Chunks“ (vorher/nachher) laden.

Man kann die Reihenfolge im Prompt rekonstruktieren, damit das LLM den Kontext versteht.

Ohne chunk_num kannst du keine zusammenhängenden Textstellen wiederherstellen.

5. section_title (Abschnittsüberschrift)
Die Überschrift oder semantische Einheit, zu der der Chunk gehört.
Beispiele:

„Was ist ein Index?“

„MongoDB: Document Model“

„ACID – Atomicity“

Warum notwendig?

Überschriften geben dem LLM zusätzliches Verständnis („dieser Text gehört zur ACID-Section“).

Erhöht die Retrieval-Qualität (da der Prompt mehr Orientierung bekommt).

Hilft bei der Strukturierung der Dokumente und bei der Suche.

section_title reduziert Halluzinationen und erhöht Präzision.


Optional (Luxus):

version

tags

difficulty

visibility (und alle möglichen anderen Attribute, s. Vorlesung)



5. Speicherarchitektur (Begründungen!)
Pflichtentscheidung:

Wo speichert ihr die Texte?

Wo speichert ihr die Embeddings?

→ Begründet stichpunktartig, warum ihr euch so entschieden habt.
(Wichtiger als die „richtige“ Entscheidung ist die BEGRÜNDUNG.)

6. Retrieval-Flow (kurz & verständlich)
Beschreibt euren Ablauf:

Frage → Embedding

Vektor-Search → relevante Chunks

Laden der Original-Chunks

Zusammenführen

Antwort erzeugen (LLM optional; ansonsten kurze manuelle Zusammenfassung)

7. Tests & Beispiele
Pflicht:

1 Beispiel-Frage

Top-3 gefundene Chunks

Warum diese relevant sind

Metriken Eurer Wahl (na ja, schaut mal in den Vorlesungsunterlagen nach ...): wie gut funktioniert Euer Ansatz (again: es geht nicht drum, dass die Ergebnisse perfekt sind, sondern Ihr demonstriert, dass Ihr ordentlich getestet und gemessen habt, ob das, was Ihr gebastelt habt, auch Euren Anforderungen entspricht! ... und wenn nicht, dann eine Analyse, woran es wohl liegt)

8. Reflexion
Max. 0.5–1 Seite:

Was würdet ihr verbessern, wenn ihr mehr Zeit hättet?

Welche Designentscheidungen waren kritisch?

C) Präsentation (20 Minuten) – Pflichtstruktur
→ Max. 20 Minuten. Danach 10 Minuten Q&A.

3. Technischer Scope: Was MUSS enthalten sein – und was NICHT
Pflicht (Minimal-Scope)
Damit besteht ihr:

2–3 Textdokumente

Einfaches Chunking

Embeddings (egal ob OpenAI, Instructor, etc.)

Mongo oder SQLite zur Dokument-Speicherung

FAISS oder PGVector für Embeddings

Ein einziger funktionaler Retrieval-Flow

Sinnvolle schriftliche Begründungen

Optional (Luxus, bringt Bonuspunkte)
Nur wenn ihr Zeit habt:

Metadaten (z. B. version, tags)

kleine Web-UI

mehrere Fragen

Ranking-Heuristiken

kleine Caching-Logik (lokal, nicht Redis)

mehrere Dokumentensammlungen (SQL vs NoSQL vs Indexing)

NICHT erlaubt / NICHT nötig (verboten)
Diese Dinge zu implementieren ist bewusst ausgeschlossen, weil sie den Scope zu sehr aufblasen würden:

❌ kein Redis
❌ kein Timescale
❌ kein Rate-Limiting
❌ keine Sessions
❌ keine komplexen Pipelines
❌ keine Optimierung (ef_search, ANN-Parameter)
❌ kein großes LLM-Backend
❌ kein Web-Server mit Frontend-Engineering
❌ keine parallelen Services

wenn ihr diese Themen aber zumindest gedanklich mit einbezieht, bzw analysiert wie/wo/wann sie ein Thema sein könnten, dann könnte das sicher auch Bonus-Punkte geben.

Das Capstone ist rein NoSQL + Mini-RAG.

4. Bewertungskriterien
1. Modellierungsentscheidungen
(30 %)
– gut begründet
– konsistent
– erkennbar, dass ihr verstanden habt, was ihr tut

2. Funktionalität des Mini-RAG
(25 %)
– es muss „einmal zuverlässig funktionieren“

3. Chunking & Datenmodell (inkl. Auswirkungen auf Datenbankstruktur und Performance)
(20 %)
– sauber
– logisch
– nachvollziehbar

4. Präsentation
(15 %)
– klar
– strukturiert
– verständlich
– funktionale Demo oder Screenshot

5. Saubere schriftliche Abgabe
(10 %)
– klar
– kohärent
– keine Copy-Paste-KI-Texte im Hauptteil

5. Hinweis: Der Schlüssel ist nicht „Programmieren“, sondern „Entscheiden“
Ihr sollt zeigen:

dass ihr NoSQL-Modelle versteht,

dass ihr Chunking sinnvoll einsetzen könnt,

dass ihr Workloads und Speicher passend verbindet,

und dass ihr einen Retrieval-Flow durchdenken könnt.

Das Capstone bewertet eure Datenkompetenz, nicht die Code-Komplexität.