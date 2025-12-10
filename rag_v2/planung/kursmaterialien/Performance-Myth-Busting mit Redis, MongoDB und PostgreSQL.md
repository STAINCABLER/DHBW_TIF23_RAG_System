Hintergrund
Ihr habt in der Laborübung die Schreibleistung von drei Systemen gemessen (jeweils 10 000 Writes):

Redis (naiv vs. Pipeline)

MongoDB (naiv vs. insert_many)

PostgreSQL (naiv mit 10 000 Commits vs. eine Transaktion)

Die Ergebnisse zeigten:

Bulk/Batching/Pipelining verändert die Performance extrem

Alle „langsamen“ Resultate kamen von Client-Overhead, nicht von der Engine

MongoDB war im „Bulk Insert“-Szenario am schnellsten

Redis war ohne Pipeline deutlich langsamer als erwartet

PostgreSQL leidet massiv unter 10 000 einzelnen Commits

In dieser Reflexion geht es darum, was diese Resultate tatsächlich bedeuten – und was nicht.

🟩 Aufgabe 1 — Interpretation der Laborergebnisse (kritisch & präzise)
Beantwortet die folgenden Fragen als Team (stichwortartig genügt):

1.1 Wo lag in euren Messungen der tatsächliche Bottleneck?
War es CPU? Die Datenbank? Das Netzwerk? Python?

Welche Hinweise aus euren Zahlen belegen das?

1.2 Warum war Redis „naiv“ (ohne Pipeline) nicht besonders schnell?
Erklärt:

was ein Roundtrip ist

warum Redis bei Einzel-SETs unterperformt

warum Redis mit Pipeline plötzlich 10–15× schneller wurde

1.3 Warum war MongoDB mit insert_many() so extrem schnell?
Diskutiert:

was ein Bulk-Insert intern bedeutet

warum dieses Szenario ein perfekter Spezialfall für Mongo ist

warum das nicht bedeutet, dass MongoDB generell schneller ist

1.4 Warum braucht PostgreSQL in einer einzigen Transaktion dramatisch weniger Zeit?
Erklärt:

was ein Commit in PostgreSQL wirklich tut (WAL, fsync, Locks)

warum 10 000 einzelne Commits 10 000× teuer sind

warum eine Transaktion einen völlig anderen Kostentreiber hat

1.5 Zieht ein erstes Zwischenfazit:
Formuliert 3 Sätze zu:

„Was sagt unser Experiment wirklich aus – und was sagt es NICHT aus?“

🟧 Aufgabe 2 — Warum ist dieser Benchmark im echten Leben unrealistisch?
Diskutiert gemeinsam:

In wie vielen realen Systemen schreibt ihr 10 000 unabhängige einzelne Werte ohne Updates weg?

Welche Praxis-Szenarien sind viel typischer?
(z. B. Session-State, Produktdaten, Rechnungen, IoT-Sensoren, Cache-Kaltstarts, Benutzerprofile…)

Formuliert 3 Beispiele aus realen Anwendungen, die dieses Labor-Beispiel nicht abbildet.

🟨 Aufgabe 3 — Workload-orientiertes Denken: Welche Fragen fehlen noch?
Euer bisheriger Test betrachtet nur einen einzigen Aspekt: große Menge Writes.

Jetzt sollt ihr überlegen, welche anderen Dimensionen man testen müsste, um wirklich sesuatu sinnvolle Architekturentscheidungen treffen zu können.

Erstellt eine Liste mit mindestens 5 weiteren Performance-Fragen, z. B.:

Wie schnell sind Reads (Redis GET vs. Mongo find vs. PG SELECT)?

Wie verhalten sich die Systeme bei Mixed Workloads (50% Read / 50% Write)?

Was passiert bei concurrent Writes?

Was passiert bei Updates statt Inserts?

Wie teuer ist ein Update auf ein Großes Dokument?

Wie wirkt sich TTL (Redis EXPIRE) auf die Last aus?

Wie beeinflusst Indexierung die Write-Performance?

Wie sieht die Latenz (P95/P99) bei hoher Last aus?

Wie skaliert das System, wenn viele Clients gleichzeitig schreiben?

Wählt aus eurer Liste die 3 wichtigsten für die Praxis aus und begründet eure Auswahl.

🟫 Aufgabe 4 — Design Thinking: neue Labor-Experimente vorschlagen
Basierend auf euren Erkenntnissen formuliert ihr mindestens zwei neue Labor-Experimente, die:

technisch interessant sind

echte Systemvergleiche ermöglichen

typische Backend-Probleme widerspiegeln

Beispiele (zur Inspiration, nicht vorgeben!):

TTL-Test: 100 000 Keys mit EXPIRE erzeugen → wie teuer ist Auto-Cleanup?

Update-Test: 10 000 Updates auf JSON-Dokumente → Verhalten bei Partial-Updates

Cache-Hit-Test: 99% Reads, 1% Writes → wer gewinnt in Latenz?

Bulk-Update-Test: 10 000 Felder eines Objekts ändern (Mongo vs. PG vs. Redis)

Mixed Workload: 70% GET, 30% SET/INSERT

IoT-Szenario: 1 000 Sensoren schreiben Werte → wie stabil sind die Systeme?

Formuliert pro vorgeschlagenem Experiment:

Ziel

Hypothese

warum es realistisch ist

welche Metriken man messen müsste

🟥 Abgabe
Ein PDF oder Markdown-Dokument pro Team mit:

Ergebnissen zu Aufgabe 1

Diskussion zu Aufgabe 2

Liste + Priorisierung zu Aufgabe 3

2–3 ausgearbeiteten Vorschlägen für Aufgabe 4