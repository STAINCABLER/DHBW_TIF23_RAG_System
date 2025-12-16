0.1 Was du am Ende dieses Kurses können wirst (Lernziele)
Nach diesem Kurs kannst du:

Datenarten analysieren (strukturierte, semi-strukturierte Dokumente, Embeddings, Ephemeral State).

Workloads richtig einordnen (z. B. Session-Data, Dokumente, Metadaten, Vektor-Suche).

Datenmodelle entwickeln, die zu echten Use Cases passen.

NoSQL-Datenbanken unterscheiden und begründet auswählen (Document Store, Key-Value Store, Vector Store).

einen Mini-RAG-Workflow designen, der Retrieval-Qualität und Speicherstruktur verbindet.

Architekturentscheidungen begründet dokumentieren und Alternativen bewerten.

Das Wichtigste:
Du lernst nicht „Syntax“, sondern „Data Engineering Denken“ – d.h. wie man aus Anforderungen technische Entscheidungen ableitet.

0.2 Warum wir RAG als Leitmotiv nutzen
RAG-Systeme sind ideal geeignet, um alle wichtigen NoSQL/Data-Engineering-Fähigkeiten zu lernen:

Dokumente → Mongo/JSON

Chunking & Metadaten → Datenmodellierung

Embeddings → Vektor-Indizes

Sessions, Rate-Limits, Cache → Key-Value (Redis)

Query Paths → Performance, Latenz, Kosten

Architektur → Polyglotte Speicherlandschaften

RAG ist hier NICHT das Ziel, sondern das didaktische Fahrzeug, um echte, realistische Entscheidungen im Data Engineering zu üben.

0.3 Wie der Kurs aufgebaut ist
Der Kurs besteht aus:

12 kurzen, klar fokussierten Modulen („Golden Nuggets“):
Die Nuggets:


NUGGET 1 — Datenarten bestimmen Zugriffsszenarien
(Was für Datenobjekte gibt es? Wie werden sie benutzt?)

NUGGET 2 — Zugriffsszenarien bestimmen Workloads
(Wie oft, wie parallel, wie intensiv passiert was?)

NUGGET 3 — Workloads bestimmen die Wahl der Datenbank
(DB-Auswahl = Risiko-Management: Konsistenz, Latenz, Lastprofil, Pfade, Operability)

NUGGET 4 — Query Paths bestimmen die Systemkosten
(Welche Operationen liegen im kritischen Pfad und dominieren die Latenz?)

NUGGET 5 — Datenmodellierung folgt Access Paths, nicht Tabellenideen
(NoSQL = Modell folgt dem Use-Case, nicht umgekehrt.)

NUGGET 6 — Chunking ist Datenmodellierung, nicht Textschneiden
(Wie man Dokumente so schneidet, dass Workload & Retrieval zusammenpassen.)

NUGGET 7 — Embeddings sind ein eigener Datentyp mit eigenem Workload
(Vektor-Indizes, ANN-Suche, Separierung der Vektor-Workloads.)

NUGGET 8 — Gute Metadaten reduzieren Komplexität und Beschleunigen Retrieval
(Metadaten als First-Class-Citizen in NoSQL/RAG.)

NUGGET 9 — Retrieval ist Query-Design, nicht Magie
(Retrieval-Pipeline als Abfolge konkreter Datenbankzugriffe.)

NUGGET 10 — Polyglotte Speicher: Document + Vector + KV
(Mindestarchitektur moderner Systeme, rationale Trennung.)

NUGGET 11 — Einfachheit schlägt Komplexität im Prototyping
(Keep it simple: jede Schicht zu früh zu optimieren macht alles schlechter.)

NUGGET 12 — Data Engineering = dokumentierte Entscheidungen
(Transparenz, Alternativen, Risiken, Begründung – Capstone-relevant.)


Jedes Modul enthält:

Big Picture – wo wir gerade im Data-Engineering-Flow sind

Kernkonzept (sehr kurz + Beispiel)

Capstone-Relevanz (konkret: Was du dafür brauchst & was bewertet wird)

Mini-Aufgabe (10–20 Minuten)

Quick-Check („Habe ich es verstanden?“)

LLM-Assist (optional)


Das Capstone-Projekt (Portfolioprüfung)
Du entwirfst ein Mini-RAG-System zum Thema Datenbanken, inkl.
– Dokumentmodell, Chunkingmodell, Embeddingspeicher, Retrieval-Flow
– Begründeter Einsatz von mind. 2 NoSQL-Technologien
– Schriftliche Ausarbeitung
– 20-minütige Präsentation

komplette Beschreibung s. ganz unten

0.4 Wie du am besten lernst (Studierenden-orientiert)
Arbeite die Module nacheinander, nicht wild durcheinander.

Lies die Beispiele, mache die Mini-Aufgaben, und beantworte die Quick-Checks.

Nutze den vorgeschlagenen LLM-Assist, um deine Entscheidungen im Capstone früh zu validieren.

Lies nicht alles auf einmal – jedes Modul ist kurz und auf ein Ziel fokussiert.

0.5 Die wichtigste Orientierungshilfe: Der Data-Engineering-Flow
Wir nutzen im ganzen Kurs eine einheitliche Struktur:

Datenarten verstehen

Workloads analysieren

Datenmodelle entwerfen

DB-Technologie auswählen

Systemdesign / Query Paths bauen

Entscheidungen dokumentieren

Jedes Modul ist ein Baustein davon.

0.6 Was im Capstone bewertet wird (explizit!)
In deiner schriftlichen Abgabe wird bewertet, ob du:

Datenarten korrekt identifizierst

Workloads richtig zuordnest

Chunking + Metadaten sauber modellierst

Vektor-Speicher begründet auswählst

Ephemeral State korrekt von persistenten Daten trennst

Query Paths nachvollziehbar beschreibst

Alternativen erkennst und begründete Entscheidungen triffst

Daher:
Jedes Modul liefert dir genau die Bausteine, die du für die Capstone-Bewertung brauchst.

0.7 Warum dieser Kurs anders ist, bzw sein soll
Weniger Theorie, mehr Anwenden auf echte Probleme.

Weniger Syntax, mehr Entscheidungslogik.

Weniger „Mongo vs Postgres“, mehr „Welcher Workload braucht welche Engine?“

Weniger Overload, mehr klarer Fokus.