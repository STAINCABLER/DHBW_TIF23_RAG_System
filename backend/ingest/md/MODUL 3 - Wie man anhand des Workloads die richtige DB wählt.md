# MODUL 3 - Wie man anhand des Workloads die richtige DB wählt

## 1. Ziel dieses Moduls

Nach diesem Modul kannst du:

- eine reale DB-Auswahl wie ein Data Engineer durchführen,
- Workloads aus Modul 2 gezielt auf DB-Grenzen abbilden,
- Risiken erkennen, die bei falscher DB-Auswahl entstehen,
- die sechs professionellen Auswahlkriterien anwenden,
- eine saubere, nachvollziehbare Entscheidung für dein Capstone-Projekt dokumentieren.

Dieses Modul verknüpft:

- die Datenarten & Zugriffsszenarien aus Modul 1
- mit den Workloads & Messwerten aus Modul 2
- und führt zur Datenbank-Auswahl.

## 2. Der zentrale Gedanke: DB-Auswahl ist immer Risiko-Management

Eine Datenbank ist geeignet, wenn keines der folgenden Risiken kritisch wird:

- **Integritätsrisiko** — Daten wären inkonsistent oder regelwidrig.
- **Workload-Risiko** — Die DB schafft die erwartete Last nicht.
- **Latenz-Risiko** — Operationen im kritischen Pfad werden zu langsam.
- **Modellierungsrisiko** — Dein Datenmodell passt nicht zur Engine.
- **Operations-Risiko** — Betrieb, Backups, Monitoring sind nicht beherrschbar.
- **Evolutions-Risiko** — Änderungen am Produkt wären später fast unmöglich.

Wenn du eine DB auswählst, entscheidest du faktisch:

„Mit welchen Risiken kann ich leben — und welche darf das System nicht haben?"

Diese Denkweise ist Standard in professionellen Architekturen.

## 🟥 3. Die sechs Kriterien, die jede professionelle DB-Auswahl bestimmen

Wir nutzen echte Industry-Kriterien, nicht „Blogpost-Mythen".

### 3.1 Konsistenzanforderungen (ACID vs. eventual)

Zentrale Frage:

„Muss diese Operation garantiert korrekt sein?"

- Wenn ja → Postgres, ACID zwingend.
- Wenn nein → Mongo oder Redis möglich.

Beispiele:

- Kundendaten (streng)
- Chat-Nachrichten (eventual)
- Rate-Limits (eventual + TTL)

### 3.2 Workload-Typ

- mixed → OLTP, Kundendaten → Postgres
- search-heavy → Embeddings → pgvector

Wenn Workload ≠ Engine-Stärken → Risiko steigt.

### 3.3 Lastprofil (Load Envelope)

Entscheidend sind:

- normale Last (Requests/s)
- Peak-Last (Spikes x2/x5/x10)
- Bursts (extrem kurze Spitzen)
- Latenzbudget (z. B. < 80 ms pro RAG-Request)

Nutze wieder deine Messwerte:

- Postgres JSONB: ~400 Reads/s (realistisch)
- MongoDB: ~700+ Reads/s
- Redis: >100k Ops/s
- pgvector: 2k–10k ANN/s

Beispiel:
Chunk Retrieval benötigt 360 Reads/s beim Peak
→ Mongo sicher, JSONB grenzwertig.

Wichtig:
Die Zahlen hier sind Illustrationen.
Für dein Capstone-Projekt zählen ausschließlich deine eigenen Messwerte (Modul 2).

### 3.4 Kritische Query-Pfade (was beeinflusst das Antwort-Zeitbudget?)

Frage:

„Welche Schritte müssen immer schnell sein?"

Beispiel Customer-Service-RAG:

kritisch für User Experience:

- Redis Rate-Limit (1–5 ms)
- Redis Session-Lookup
- pgvector ANN-Suche (~20–40 ms)
- Mongo Chunk Reads (~20–50 ms)

NICHT kritisch:

- Logging
- Analytik
- Monitoring
- Preprocessing

→ Wenn eine DB im kritischen Pfad zu langsam ist, scheidet sie aus.

### 3.5 Modellierungsrisiko (passt dein Modell in diese Engine?)

Beispiele:

- Mongo wird ineffizient, wenn du viele Teil-Updates brauchst
- Redis kann keine komplexen Queries
- Postgres JSONB ist schlecht für riesige Dokumente

### 3.6 Operability (Betreibbarkeit)

Professionelle Systeme gehen kaputt, wenn Operability ignoriert wird.

Fragen:

- Kann das Team Backups fahren?
- Sind Upgrades einfach?
- Wie schwer ist Monitoring?
- Ist Hochverfügbarkeit trivial oder komplex?
- Ist Persistence (Redis!) zuverlässig konfigurierbar?

Beispiel:
Redis ist ultraschnell, aber nur sicher mit RDB/AOF-Konfiguration und Replika-Setup.

## 🟥 4. Der professionelle Entscheidungsprozess (5 Schritte)

Die Industrie nutzt genau diesen Ablauf:

### Schritt 1 — Datenobjekte bestimmen (Modul 1)

z. B.:
Chunk, Embedding, Kundendatensatz, Chatnachricht, Session-Item

### Schritt 2 — Zugriffsszenarien bestimmen (Modul 1)

z. B.:
6 Chunk-Reads, Append-Write, Profil-Update, Session-Lookup

### Schritt 3 — Workloads quantifizieren (Modul 2)

Nutze deine Messwerte.

Beispiel:
40 Requests/s × 6 Chunk-Reads = 240 Chunk Reads/s
→ Mongo sicher (gemessen), JSONB grenzwertig (gemessen)

### Schritt 4 — die sechs Kriterien anwenden (dieses Modul)

Beispiel:

- Postgres → ACID gut, aber JSONB bei 240 Reads/s knapp
- Mongo → read-heavy stark, eventual consistency ausreichend
- pgvector → ANN performant
- Redis → Sessions extrem schnell

### Schritt 5 — Entscheidung dokumentieren (Capstone)

Eine vollständige Entscheidung enthält:

- die Alternativen
- die Workloads
- die Risiken
- die begründete Auswahl
- die Ausschlussgründe

Genau das wird bewertet.

## 🟥 5. Beispiel: Auswahl für ein Customer-Service-RAG

### Objekt 1 — Kundendaten

- Konsistenz: Hoch
- Workload: mixed
- Pfad: kritisch
- Modell: relational

→ Postgres

### Objekt 2 — Chunks

- Konsistenz: gering
- Workload: read-heavy
- Pfad: kritisch
- Modell: großes semistrukturiertes Dokument

→ MongoDB

### Objekt 3 — Embeddings

- Konsistenz: gering
- Workload: search-heavy
- Pfad: kritisch
- Modell: Vektoren

→ pgvector

### Objekt 4 — Session / Rate-Limit

- Konsistenz: gering
- Workload: write-heavy, tiny ops
- Pfad: kritisch
- Modell: Key-Value

→ Redis

## 🟥 6. Capstone-Verpflichtungen

In deiner Ausarbeitung musst du:

- ✔ Datenobjekte definieren
- ✔ Zugriffsszenarien bestimmen
- ✔ Workloads quantifizieren
- ✔ deine Messwerte anwenden
- ✔ die sechs Kriterien nutzen
- ✔ Alternativen ausschließen
- ✔ die finale Entscheidung begründen

Ohne diese Struktur ist die Abgabe unvollständig.

## 🟥 7. Aufgaben (Mini, 10–20 Minuten)

### Aufgabe 1 — Engine auswählen

Gegeben:

- 240 Reads/s (Peak)
- Chunks à 3–5 KB
- Latenzbudget: <80 ms

Welche Engine?

**Lösung:** MongoDB

**Begründung:** read-heavy, Dokumentstruktur, hohe Durchsatzfähigkeit

(Hinweis: Nutze später deine eigenen Messwerte!)

### Aufgabe 2 — Embedding-Engine

Gegeben:

- 4 000 ANN-Queries/s
- Filter nach Produktfamilie
- kritische Latenz

Welche Engine?

**Lösung:** pgvector

## 🟥 8. Häufige Fehlentscheidungen

- „Postgres ist immer sicher."
- „Mongo ist flexibler."
- „Redis ist schnell, also ideal."
- „Ich benchmarke ein paar Inserts, das reicht."
- „Wir nehmen die DB, die wir kennen."

Alle fünf ignorieren Workloads, Risiken und Pfade.

## 🟥 9. LLM-Assist (optional)

Beispiel-Prompts:

- „Welche Risiken übersehe ich bei dieser DB-Auswahl?"
- „Welche kritischen Query-Pfade habe ich nicht berücksichtigt?"
- „Welche Konsistenzanforderungen gelten für mein Datenobjekt?"

LLMs ersetzen nicht die Messungen —
sie helfen dir, bessere Fragen zu stellen.
