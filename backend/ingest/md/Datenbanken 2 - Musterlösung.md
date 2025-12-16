# Musterlösung

Musterlösung – E-Commerce RAG System: KONKRETE Definition des Szenarios
Bitte kopieren:

## 📦 Fiktives E-Commerce-Szenario (klar definiert)

Ihr baut ein RAG-System für den Kundensupport eines mittelgroßen Online-Händlers:

### Produkte (Katalog)

- Elektronik (Smartphones, Laptops, Kopfhörer)
- Haushaltsgeräte (Staubsauger, Kaffeemaschinen)
- Kleidung (Jacken, Schuhe)

Sortiment: 8.500 Produkte

### Daten, die existieren

- Produktbeschreibungen (HTML → Text)
- Produktattribute (Preis, Größe, Gewicht, Garantie)
- Betriebsanleitungen (PDF → Text → Chunks)
- Retourenrichtlinien (Text)
- Kundenkonten (SQL)
- Bestellungen und Zahlungen (SQL)
- Supporttickets (JSON)
- Chatverläufe mit Kunden (JSON, append-only)

### Was der Support leisten kann

- "Wo ist mein Paket?"
- Rückgabe/Retoure erklären
- Technische Produktfragen (z. B. „Wie entkalke ich XY?")
- Fehlerdiagnose („Meine Kaffeemaschine blinkt gelb…")
- Preisinformationen
- Garantie- und Seriennummernfragen
- Produktvergleiche („Welches Headset ist leiser?")

### Lastszenario (realistisch, nicht akademisch)

- 120 Supportmitarbeiter weltweit
- Jeder bearbeitet ~2 Chats gleichzeitig
- 70 Kund*innen gleichzeitig im Chat
- Durchschnitt: 1 RAG-Query pro 6 Sekunden pro aktivem Chat

→ ~12 RAG-Queries pro Sekunde im Gesamtsystem

**Jeder RAG-Request benötigt:**

1. Rate Limit prüfen (Redis)
2. Session Context laden (Redis/Mongo)
3. Query-Preprocessing (kein DB-Zugriff)
4. Vektor-Search auf Chunks (pgvector)
5. Dokumente nachladen (Mongo/JSONB)
6. Produktmetadaten prüfen (PG)
7. Berechtigungen prüfen (PG)
8. Antwort-Komponenten cachen (Redis)
9. Logging (Timescale/PG)

→ pro Anfrage 8–12 DB-Operationen

## Ok, und was bedeutet es in der Praxis 8-12 DB Operationen zu haben?

Modellierung des E-Commerce-Support-RAG-Systems (konkreter Flow)

**Ziel dieses Abschnitts:** Ihr seht an einem ganz konkreten Beispiel, wie viele Einzelschritte ein einziger Support-Request tatsächlich hat – und warum dabei mehrere Datenbanken beteiligt sind.

## 🧩 Ausgangspunkt: Ein konkreter Support-Use-Case

Ein Kunde schreibt in den Chat:

„Meine Kaffeemaschine Modell X blinkt gelb, was soll ich tun?"

Der Support-Agent arbeitet in einem internen Web-Tool, das im Hintergrund ein RAG-System nutzt.

Das System soll:

1. Prüfen, ob der Request zulässig ist (Rate-Limits, Missbrauch).
2. Den aktuellen Chat-Kontext kennen (vorherige Nachrichten im Verlauf).
3. Relevante Dokumentstellen finden (Produktbeschreibung, Anleitung, Troubleshooting-Artikel).
4. Prüfen, ob der Support-Agent für diesen Kunden / diese Daten berechtigt ist.
5. Die Antwort des LLM loggen (für Monitoring und Audit).

Daraus ergibt sich ein konkreter Request-Flow.

## 🔁 Schritt-für-Schritt-Flow eines einzelnen RAG-Requests

Wir gehen bewusst granular vor – das ist das Modell, auf dem später die 8 Fragen aufbauen.

## 0. HTTP-Request trifft beim Backend ein

Eingehende Anfrage: POST /support/rag-answer

Enthält: Session-Token, User-ID, Agent-ID, Frage-Text, evtl. Produkt-ID.

Noch kein Datenbankzugriff.

## 1. Rate-Limit prüfen (Redis INCR + EXPIRE)

**Warum überhaupt Rate-Limits?**

- Schutz vor Bots / Abuse / Fehlkonfigurationen
- Kostenkontrolle bei LLM-Calls
- Stabilität des Systems

**Typisches Pattern:**

Key: "ratelimit:{user_id}:{minute}"

- INCR key → Zählt, wie viele Requests in diesem Zeitfenster schon kamen.
- EXPIRE key, 60 → Nach 60 Sekunden ist der Zähler weg.

**Konkrete DB-Operationen:**

- INCR ratelimit:12345:2025-11-24T10:15
- EXPIRE ratelimit:12345:2025-11-24T10:15, 60

Wenn INCR z. B. > 30 ist → Request wird abgelehnt.

👉 Das ist der „Redis INCR" aus den späteren Antworten.

## 2. Session-Kontext laden (Redis GET / ggf. HGETALL)

**Warum Session-Kontext?**

- Damit das LLM den bisherigen Gesprächsverlauf kennt („Ich hatte doch vorhin schon gefragt…").
- Um z. B. Sprachpräferenzen, gewählte Produktkategorie, Kunde vs. Gast zu kennen.

**Typischer Key:** "session:{session_id}"

**Wert:** kleines JSON mit den letzten N Nachrichten oder Referenzen darauf.

**DB-Operation:**

GET session:abc123

Wenn Session nicht vorhanden → neue Session anlegen.

👉 Das ist der „Session auslesen"-Teil in den Antworten.

## 3. Query zu Embedding machen & Vektor-Suche (pgvector)

Der Text „Meine Kaffeemaschine X blinkt gelb…" wird in einen Embedding-Vektor umgerechnet (in der Applikation, nicht in der DB).

Dann:

**pgvector-Query:**

```sql
SELECT doc_id, chunk_id, 1 - (embedding <=> $query_vec) AS score
FROM chunks
WHERE product_family = 'Kaffeemaschine'
ORDER BY embedding <-> $query_vec
LIMIT 8;
```

1 ANN/Vector-Query pro RAG-Request

Ergebnis: Liste von Chunk-IDs mit Scores

👉 Das ist der „pgvector ANN-Search" aus den Antworten.

## 4. Original-Chunks nachladen (Mongo oder PG JSONB)

Die Chunks, auf die doc_id + chunk_id verweisen, werden jetzt geladen:

**Beispiel Mongo-Dokument:**

```json
{
  "_id": "...",
  "doc_id": "manual_X_de",
  "chunk_id": 42,
  "text": "Wenn die gelbe LED blinkt, entkalken Sie das Gerät wie folgt...",
  "product_id": "KM-1234",
  "tags": ["troubleshooting", "entkalken"]
}
```

Üblicherweise:

- 3–8 Chunk-Dokumente pro RAG-Request
- 1–2 Mongo-Queries (mit $in auf chunk_id)

👉 Das sind die „Chunk-Fetches" aus den Antworten.

## 5. Produkt-Metadaten & Berechtigungen in Postgres prüfen

**Metadaten:**

- Produkt existiert?
- Produkt noch im Sortiment?
- Regionale Unterschiede? (EU vs. US-Version)

**SQL-Beispiel:**

```sql
SELECT p.id, p.name, p.region, p.obsolete
FROM products p
WHERE p.id = $product_id;
```

**Berechtigungen (RBAC):**

- Darf dieser Agent dieses Ticket sehen?
- Gehört der Kunde zu dieser Region?
- Darf diese Information (z. B. Garantiedetails) angezeigt werden?

**SQL-Beispiel:**

```sql
SELECT 1
FROM agent_permissions ap
JOIN customers c ON c.region = ap.region
WHERE ap.agent_id = $agent_id
  AND c.id = $customer_id;
```

👉 Das ist der Teil „Produktmetadaten + Berechtigungsprüfung in Postgres".

## 6. Antwort generieren & kurzzeitig cachen (Redis SETEX)

Das LLM produziert eine Antwort. Um Folgerequests schneller zu machen (z. B. bei „Kannst du das anders formulieren?"), kann man die Antwort oder die Retrieval-Resultate im Cache ablegen.

**Beispiel:**

- Key: "ragcache:{session_id}:{hash(user_question)}"
- Wert: Antworttext + verwendete Chunks
- TTL: z. B. 120 Sekunden

**DB-Operation:**

SETEX ragcache:abc123:xyz 120 {json-payload}

👉 Das ist das „SETEX/Caching", von dem später die Rede ist.

## 7. Chat-History fortschreiben (Mongo)

Die neue Nachricht des Agenten wird dem Chat-Verlauf hinzugefügt:

```json
{
  "session_id": "abc123",
  "customer_id": "C987",
  "messages": [
    { "from": "customer", "ts": "...", "text": "..." },
    { "from": "agent", "ts": "...", "text": "..." }
  ]
}
```

Je nach Modellierung:

- Ein updateOne mit $push auf messages
- Oder Einfügen eines neuen Message-Dokuments

👉 Das ist der „Chat-Append"-Teil in Mongo.

## 8. Logging / Monitoring (Timescale / PG)

Für Monitoring & Auditing wird ein Logeintrag geschrieben:

- Timestamp
- Agent-ID
- Kunden-ID
- Antwortdauer (ms)
- Anzahl der verwendeten Chunks
- Fehler? (ja/nein)

**Beispiel Timescale-Insert:**

```sql
INSERT INTO support_logs (ts, agent_id, customer_id, latency_ms, chunks_used, error)
VALUES (now(), $agent, $customer, $latency, $chunks, false);
```

👉 Das ist das „Timescale INSERT → Log".

## 📌 Zusammenfassung des Ein-Request-Flows in DB-Operationen

Für eine einzige Frage des Kunden:

1. Redis: INCR + EXPIRE
2. Redis: GET (Session)
3. pgvector: 1 ANN-Query
4. Mongo: 1–2 Queries (3–8 Chunks)
5. Postgres: 1–2 Queries (Metadaten + Permission)
6. Redis: SETEX (Cache)
7. Mongo: updateOne oder insertOne (Chat)
8. Timescale: INSERT (Log)

→ 8–14 DB-Operationen pro RAG-Request, je nach Details.

Das ist exakt die Basis, auf der später die Musterantworten zu Frage 2 („Wie viele DB-Operationen…") aufbauen.

## 🔷 Abschnitt: Von RAG-Requests/s zu DB-Ops/s – warum das TROTZ 10k writes/s relevant ist

**Ziel dieses Abschnitts:** Ihr versteht, warum „210 DB-Operations pro Sekunde" nicht einfach bedeutungslos sind, obwohl ihr lokal 10.000 Inserts/s gemessen habt.

### 1️⃣ Unterschied: Microbenchmark vs. echter Request-Mix

**Eure Benchmarks:**

- 10.000 Inserts in Mongo mit insert_many → sehr schnell
- 10.000 Inserts in Postgres in einer Transaktion → auch ordentlich
- 10.000 Redis-SETs per Pipeline → ebenfalls sehr schnell

**Aber:**

Das waren jeweils optimierte Bulk-Szenarien:

- Ein Datentyp
- Eine Operation
- Keine parallelen User
- Kein Netzwerk
- Keine zusätzlichen Indizes
- Keine Permission-Checks
- Kein Logging
- Kein LLM im Loop

Im echten System ist jeder Request ein bunter Mix aus:

- leichten Operationen (INCR, GET)
- mittelschweren Operationen (Mongo-Reads, einfache SELECTs)
- teuren Operationen (ANN-Search, Joins)

### 2️⃣ DB-Operationen sind nicht gleich „Kostenlos"

Ihr habt oben gesehen:

- Ein Redis INCR ~ Mikrosekunden-Bereich
- Eine pgvector-ANN-Query ~ mehrere Millisekunden (abhängig von Index, Dimension usw.)
- Ein Mongo-Read mit kalten Daten → 10–50ms
- Ein Postgres-Join unter Last → 5–20ms

Wenn ihr jetzt sagt:
„Wir haben 15 RAG/s und damit 120–210 DB-Ops/s"
ist die entscheidende Frage:

**Wie viele davon sind „billige" Ops und wie viele „teure"?**

Denn ein System mit:

- 200 × INCR/s (Redis) ist langweilig
- 200 × ANN-Search/s (pgvector) ist ernstzunehmende Last

### 3️⃣ Kritischer Pfad vs. Luxus-Pfad

Nicht jede Operation ist gleich kritisch.

- Wenn das Logging 1 Sekunde später geschrieben wird → nicht so schlimm.
- Wenn das Rate-Limit 500ms braucht → Chat wirkt kaputt.
- Wenn ANN-Search manchmal 300ms statt 40ms dauert → der ganze Dialog wirkt träge.

**Deshalb:**

Wir zählen Ops/s nicht nur als „Menge",

sondern fragen: Welche liegen im kritischen Pfad für die User Experience?

### 4️⃣ Parallelität und Skalierung

Lokal habt ihr getestet: ein Prozess, eine DB, keine echte Parallelität mit 100 Usern.

Im echten System:

- mehrere gleichzeitige Requests
- Threads / Worker / Container
- mehrere Datenbanken
- Netzwerk-Hops zwischen Services

→ Die effektive Kapazität pro DB hängt davon ab, wie gut sie parallel arbeiten kann, ob sie CPU-bound oder IO-bound wird, und ob ihr Spitzenlast abfangen könnt.

### 5️⃣ Warum die Zahl 120–210 DB-Ops/s trotzdem Gold wert ist

Sie ist der Startpunkt für:

- Dimensionierung (Wie viele Instanzen/Container?)
- Risikobewertung (Wo knallt es zuerst?)
- Architekturauswahl („Kann ich Rate-Limits wirklich in Postgres machen? → Nein.")
- Priorisierung (Was optimiere ich zuerst? ANN-Index, Redis, Mongo?)

Ohne diese Größenordnung bleibt alles gefühlt:

„Mongo ist doch schnell genug… auf meinem Laptop."

Mit dieser Größenordnung könnt ihr gezielt argumentieren:

„Rate-Limits gehören in Redis, weil 15 RAG/s × 2 Redis-Calls × 5er Sicherheitsfaktor → 150 ops/s. Das ist trivial für Redis, aber für Postgres wären das 150 zusätzliche Sync-Writes/s im kritischen Pfad – unnötig teuer und fehleranfällig."

## 🟦 TEIL 1 – Musterlösung zu den 8 Last-/Scaling-Fragen

Zu jeder Frage bekommt ihr:

- schlechte Antwort (falsch oder unpräzise)
- gute Antwort (korrekt)
- exzellente Antwort (technisch präzise + begründet + numerisch)

## 1. Wie viele RAG-Requests pro Sekunde erwartet ihr?

**Schlecht:**
„Kommt drauf an, aber bestimmt nicht viele."

**Gut:**
„12 Requests pro Sekunde, ausgehend von 70 parallelen Chats und einer Anfrage alle 6 Sekunden."

**Exzellent:**
„Bei 70 parallelen Chats × 1 RAG-Query alle 6s entstehen ~12 Queries pro Sekunde (70/6 ≈ 11.7). Dazu kommen 2–3 weitere Queries pro Sekunde durch Parallelaktionen wie Ticketupdates. Wir rechnen mit 15 RAG-Requests pro Sekunde unter Normalbetrieb und bis zu 40 unter Lastspitzen (Sale-Events, Black Friday)."

## 2. Wie viele DB-Operationen verursacht EIN einzelner RAG-Request?

**Schlecht:**
„Nur eine für die Vektor-Suche."

**Gut:**
„8–10 DB-Operationen, weil mehrere Systeme beteiligt sind."

**Exzellent:**
„In diesem Use-Case erzeugt ein RAG-Request:

- Redis INCR → Rate-Limit
- Redis GET → Session Context
- PG/pgvector → ANN-Search
- Mongo → 3–5 Chunk-Fetches
- PG → Produktmetadaten
- PG → Berechtigungsprüfung
- Redis SETEX → Cache
- Timescale INSERT → Log

= 8–14 DB-Operationen pro RAG-Request
Bei 15 RAG/s → 120–210 DB-ops/s."

## 3. Welche DB wird am stärksten belastet? Warum?

**Schlecht:**
„Die Vektor-DB, weil die wichtig ist."

**Gut:**
„Redis, weil Rate-Limits und Sessions jede Anfrage betreffen."

**Exzellent:**
„Redis wird am stärksten belastet (~30–60 ops/s), da jede Anfrage:

- Rate-Limit aktualisiert
- Session ausliest
- Cache invalidiert oder beschreibt

pgvector ist zweiter (10–20 ops/s), aber mit teureren Einzeloperationen.
Mongo wird je nach Chunking 20–40 ops/s sehen (mehrere kleine Reads)."

## 4. Welche DB ist Single Point of Failure?

**Schlecht:**
„Eigentlich keine, wir können ja replizieren."

**Gut:**
„Redis ist kritisch, weil Rate-Limiting und Sessions dort liegen."

**Exzellent:**
„Redis ist operational der kritischste Pfad, weil ohne Rate-Limits der Schutz vor Spam-Bots entfällt und ohne Session-State die gesamte Chat-Kohärenz bricht. pgvector ist kritisch für die Antwortqualität, aber Redis ist kritisch für Systemstabilität."

## 5. Welche DB braucht horizontales Scaling?

**Schlecht:**
„pgvector, weil Machine Learning."

**Gut:**
„Mongo, weil es viele Reads bekommt."

**Exzellent:**
„Mongo skaliert horizontal am sinnvollsten, weil:

- Chunk-Fetches sind read-heavy
- Laststeigerungen gehen linear in die Breite
- Mongo hat eingebautes Sharding

pgvector kann replizieren, aber Sharding ist komplexer.
Redis kann replizieren oder clusterisieren — hier könnte horizontales Scaling nötig werden, wenn Sessions & Rate-Limits stark steigen."

## 6. Welche Zugriffe sind besonders anfällig für Latenzspitzen?

**Schlecht:**
„Die Vektor-DB."

**Gut:**
„ANN-Search kann Spitzen erzeugen."

**Exzellent:**
„Latenzspitzen betreffen v. a.:

- Redis GET/SET (wenn die Netzwerk-Latenz steigt → domino effect)
- Mongo Chunk-Fetches (bei Cold Reads → E/A Peak)
- pgvector ANN-Search (bei Misses im RAM → 3–10× langsamer)

Besonders kritisch: Redis, weil der gesamte Dialog-Flow daran hängt."

## 7. Welche Zugriffe müssen p99 < 100 ms bleiben?

**Schlecht:**
„Alle."

**Gut:**
„Redis und Vektor-Search."

**Exzellent:**
„Für ein Supportsystem gelten folgende p99-Ziele:

- Redis Rate-Limit + Session Read: <5ms
- pgvector ANN: <40ms
- Chunk-Fetch (Mongo): <50ms
- Berechtigungen/Metadata (PG): <20ms

Alles zusammen muss p99 < 100ms bleiben, sonst ruckelt der Chat."

## 8. Welche Operationen sind parallelisierbar, welche NICHT?

**Schlecht:**
„Fast alles ist parallelisierbar."

**Gut:**
„Manche DBs lassen Anfragen parallel verarbeiten."

**Exzellent:**

**Parallelisierbar:**

- Mongo Chunk-Fetches (horizontal skalierbar)
- PG Metadata Checks (CPU-bound, gut parallelisierbar)
- Redis Reads (bei Clusterbetrieb verteilbar)

**Nicht parallelisierbar (oder nur schwer):**

- ANN-Search pro Query (kann nicht in mehrere Maschinen aufgespalten werden ohne Sharding)
- Session Updates (Redis INCR / SETEX → lock-free aber SEQUENTIELL am Key)

## 🟧 TEIL 2 – Musterlösung zu den 6 Original-Fragen

## 1. Welche Datenarten existieren?

**Schlecht:**
„Texte und Embeddings."

**Gut:**
„Dokumenttexte, Produktdaten, Bestellungen, Chats."

**Exzellent:**
„Wir haben:

- Dokumente (Produktbeschreibungen, Anleitungen) → Mongo/JSON
- strukturiertes SQL (Kunden, Bestellungen, Zahlungen) → Postgres
- Zeitreihen (LLM-Latenzen, Errors) → Timescale
- Anhänge (PDFs) → Object Store
- Chat-Historien (append-only JSON) → Mongo
- Vektoren (Embeddings) → pgvector
- flüchtige Keys (Session, Rate-Limit, Cache) → Redis"

## 2. Wo entsteht Konsistenzdruck?

**Schlecht:**
„Bei wichtigen Daten."

**Gut:**
„Bei Zahlungen, Kundenkonten."

**Exzellent:**
„Konsistenz ist zwingend notwendig bei:

- Bestellungen & Zahlungen (ACID)
- Produktverfügbarkeit (Lagerbestand)
- Rollen/Berechtigungen (Support darf nur bestimmte Infos sehen)
- Ticket-Verknüpfungen (Wer hat welches Problem?)

Alles gehört in Postgres."

## 3. Wo entsteht flüchtiger State?

**Schlecht:**
„Im Cache."

**Gut:**
„Sessions und Cache."

**Exzellent:**
„Flüchtige Daten:

- Rate-Limits (Redis TTL 1–60 Sekunden)
- Chat-Session-Context (Redis)
- Prompt-Caches (Redis SETEX)
- LLM-Error-Counters (Redis INCR)
- intermediate retrieval results (Redis 100–500ms TTL)"

## 4. Wo werden Vektoren benötigt?

**Schlecht:**
„Für die Suche."

**Gut:**
„Für Ähnlichkeitssuche über Dokumente."

**Exzellent:**
„Wir speichern Embeddings für:

- Produktbeschreibungen
- Anleitungs-Abschnitte
- Troubleshooting-Abschnitte
- frühere Lösungsdialoge
- FAQ-Einträge

Diese liegen in pgvector, damit Metadaten wie Kategorie, Hersteller, Version filterbar bleiben."

## 5. Wo braucht ihr Logs / Audit Trails?

**Schlecht:**
„Überall."

**Gut:**
„Bei Supportaktionen und Datenzugriff."

**Exzellent:**
„Audit Trails sind erforderlich bei:

- Zugriff auf Kundendaten (DSGVO)
- Änderung von Bestellstatus
- Anzeigen von Rücksendedetails
- Systemfehlern
- LLM-Response-Latenz
- Prompt-Protokollen

Wir speichern strukturierte Logs in Timescale (Zeitreihe) und sensitive Events in PG."

## 6. Welche Teile müssen logisch getrennt werden?

**Schlecht:**
„Frontend und Backend."

**Gut:**
„Vector DB, SQL, Redis."

**Exzellent:**
„Wir trennen logisch:

- Session Layer (Redis)
- Retrieval Layer (Vektoren) (pgvector)
- Document Store (Mongo / JSONB)
- OLTP Backend (Postgres)
- Logging / Monitoring Layer (Timescale)
- LLM Orchestration Layer
- Caching / Rate-Limit Layer (Redis)

Diese Separation verhindert:

- Datenvermischung
- Deadlocks
- Overload auf einzelnen Systemen
- inkonsistente Datenmodelle"

## 🟥 TEIL 3 – KLARE Differenzierung: p99 Latenz vs. Latenzspitzen

**Latenzspitzen:**

- Unregelmäßige Ausreißer
- z. B. Cold Read, GC Pause, Docker I/O
- können Sekunden dauern
- selten, aber gefährlich wenn sie kritische Pfade betreffen

**p99 Latenz:**

- Die Latenz, die 99 % aller Anfragen unterschreiten
- das wichtigste SLA-Kriterium
- definiert die wahrgenommene Systemgeschwindigkeit

**Vergleich im Use-Case:**

| Bereich | Latenzspitzen | p99 Ziel |
|---------|---------------|----------|
| Redis Rate-Limit | selten: 20–40ms | <5ms |
| pgvector ANN | Cold RAM spike: 100–300ms | <40ms |
| Mongo Chunk Read | Disk Miss: 50–80ms | <50ms |
| PG Metadata | Lock-Wait: 20ms | <20ms |
