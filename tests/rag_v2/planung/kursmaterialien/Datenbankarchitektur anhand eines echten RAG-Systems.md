Warum dieses Projekt NICHT eure Perspektive braucht, sondern echte Systemarchitektur
Wenn man nur aus der eigenen Perspektive denkt ―
„Ich brauche doch nur Text, Embeddings und eine DB…“ ―
dann wird jedes System extrem klein, unrealistisch und technisch uninteressant.

In der Realität ist ein RAG-System kein Studenten-Sideproject, sondern ein klassisches Enterprise-System, das oft aus 8–12 klar getrennten Komponenten besteht:

Dokumentversionen

User-Berechtigungen

sensible oder vertrauliche Daten

Chat-Historien

Caches

Rate-Limits

strukturierte Metadaten

Logs & Analytics

Zeitreihen (z. B. LLM Response-Times)

Vektor-Indizes

Auditing & Compliance

Ihr baut also kein RAG für euch selbst,
sondern ein System, das echten Anforderungen standhalten muss.

🎯 Damit ihr NICHT in die „Studentenperspektive“ fallt, bekommt ihr 5 realistische Use-Cases.
Ihr wählt später einen davon aus.

Hier sind sie — alle basieren auf realen industriellen oder behördlichen Anforderungen:

Use Case 1 — Support-Assistenzsystem für eine Bank
Daten:

Verträge (PDF + Text)

Kundenprofile (strukturiert)

Produkte (dokumentenartig)

interne Wissensdatenbank
Workloads:

strenge Berechtigungen (ACID)

Chats & Sitzungsverläufe (JSON)

Sensible Daten → Audit Logs (append-only)

Rate-Limits (Redis)

Use Case 2 — RAG für einen Maschinenhersteller
Daten:

Handbücher

Wartungsprotokolle

Sensordaten als Zeitreihen

Embeddings aus Dokumenten
Workloads:

viel Chunking

viel Zeitreihe (Timescale/PG)

multi-level Permissions (PG)

Caches für Suchergebnisse (Redis)

Use Case 3 — RAG für ein soziales Netzwerk (Moderation)
Daten:

Chatlogs

User Reports

Richtlinien/Content Policy

Embeddings der verstößigen Inhalte
Workloads:

extrem write-heavy Chatflows (Mongo)

metastabile Sessions (Redis)

semantische Suche (pgvector/Mongo)

Logging (PG/TS)

Use Case 4 — RAG für E-Commerce Produkt- und Kundensupport
Daten:

Produktdaten (JSON)

Bestellungen & Zahlungen (SQL)

Chat-Verläufe (Mongo)

Embeddings über Beschreibungen
Workloads:

ACID für Zahlungen

Fulltext + Vektor für Produkte

Retrieval Cache (Redis)

Rate-Limit für Bots

Use Case 5 — Behördliche Knowledge QA (mit strengen Compliance-Anforderungen)
Daten:

Verordnungen

Bescheide

Akten mit Versionierung

interne Handreichungen
Workloads:

Immutable Dokumentversionen (PG)

Embeddings (Mongo oder PG)

Auditlogs (Timescale)

Sessions & TTL (Redis)

💡 Wichtig: Die Use Cases sind so gewählt, dass sie ALLE Komponenten erzwingen.
Damit verschwindet das Problem:
„Ich brauche doch nur Text, also Mongo reicht…“

Sondern es tritt stattdessen klar hervor:

wo Struktur wichtig ist

wo Flexibilität wichtig ist

wo Geschwindigkeit wichtig ist

wo ACID nicht verhandelbar ist

wo TTL wichtig ist

wo Time-Series wichtig ist

wo Vektorsuche nötig ist

Ihr könnt gar nicht alles in einer einzigen DB lösen → genau das ist der Lerneffekt.


1. Wie viele RAG-Requests pro Sekunde erwartet ihr in eurem Use Case?
Baut ein realistisches Szenario.
(E-Commerce? → 50 Req/s.
Social? → 500 Req/s.
Bank? → 5–20 Req/s.)

2. Wie viele DB-Aufrufe verursacht EIN RAG-Request in eurem Design?
Zerlegt in:

Embedding Suche

Chunk-Fetches

Metadata-Checks

Session Updates

Rate-Limits

Logging

Caching

→ multipliziert ergibt die echte Systemlast.

3. Welche DB wird pro Sekunde am meisten belastet? Warum?
Ist es PG? Redis? Mongo?
bitte begründen.

4. Welche DB ist im Fehlerfall der Single Point of Failure?
bloss nicht Redis vergessen;-)

5. Welche DB benötigt horizontales Scaling? Welche nicht?
Begründung basierend auf Workload.

6. Welche DB kann Latenzspitzen NICHT abfedern?
Redis puffert, PG drosselt, Mongo queued.

7. Welche Zugriffe sind kritisch für p99 Latenz (<100ms)?
nachdenken über Query-Pfade.

8. Welche Queries sind extrem parallelisierbar, welche NICHT?
z. B. Vektor-Search ist NICHT parallelisierbar ohne Sharding.




📘 Schritt 1 Aufgabe:
Wählt einen der 5 Use Cases aus.

Beantwortet nur diese Fragen (max. 10 Minuten):

Welche Datenarten existieren (Dokumente, Zeitreihen, JSON, relational)?

Wo entsteht Konsistenzdruck (Compliance, Zahlungen, Rollen)?

Wo entsteht flüchtiger State (Sessions, Caches, Rate Limits)?

Wo werden Vektoren benötigt?

Wo braucht ihr Logs/Audit Trails?

Welche Teile müssten logisch getrennt werden?




Artefakt: „Initial System Map“ (Miro oder 1–2 Slides).