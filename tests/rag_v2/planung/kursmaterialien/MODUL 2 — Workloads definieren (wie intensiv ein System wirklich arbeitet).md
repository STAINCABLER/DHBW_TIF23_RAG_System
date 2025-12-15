1. Ziel des Moduls
Nach diesem Modul kannst du:

aus Zugriffsszenarien echte Workloads ableiten,

verstehen, warum Workloads ohne Zahlen wertlos sind,

Anforderungen exakt formulieren (Reads/s, Writes/s, Latenzbudgets),

Messwerte sammeln, die später für die DB-Auswahl entscheidend sind,

kritische Operationen identifizieren.

Dieses Modul ist die Brücke zwischen
„Wie nutzen wir die Daten?“ (Modul 1)
und
„Welche Datenbank kann das leisten?“ (Modul 3).

2. Warum Workloads notwendig sind
Viele glauben, man könne Datenbanken so auswählen:

„Dokumente → Mongo.“
„Vektoren → Vektor-DB.“
„Key-Value → Redis.“

Das ist falsch.

Warum?

Weil Datenbanken nicht wegen ihrer Typen, sondern wegen ihrer Grenzen scheitern:

zu viele Writes

zu große Peaks

zu hohe Parallelität

zu niedrige Toleranz für Latenz

zu starke Anforderungen an Konsistenz

Um diese Grenzen zu verstehen, brauchst du:

→ Workloads mit echten Zahlen.
Begriffe wie
„hoch“, „niedrig“, „viel“, „selten“, „oft“
sind keine Workloads.

🟦 3. Die 4 Dimensionen eines Workloads
Ein Workload beschreibt wie intensiv ein Zugriffsszenario im System ausgeführt wird.

3.1 Häufigkeit
Wie oft passiert die Operation?

Beispiele:
– 12 Reads/s
– 500 Inserts/min
– 2 Updates/Tag

3.2 Parallelität
Wie viele Nutzer/Requests gleichzeitig?

Beispiele:
– 5 aktive Agents
– 40 parallele Anfragen
– 200 gleichzeitige ANN-Suchen

3.3 Änderungsintensität
Wie stark verändern sich die Daten?

Beispiele:
– nur lesen
– häufiges Überschreiben
– Append-only
– Bulk-Ingest

3.4 Kritikalität / Fehlertoleranz
Was passiert, wenn die Operation:

200 ms dauert?

3 Sekunden dauert?

verloren geht?

verdoppelt wird?

verspätet eintrifft?

Die Antwort bestimmt später die Wahl zwischen
– strenger Konsistenz
– eventual consistency
– asynchronem Logging
– Caching
– Queueing

🟥 4. Aus Zugriffsszenarien werden Workloads
Ein Zugriffsszenario aus Modul 1:

„Dokument + read-heavy → Chunk Retrieval“

wird erst durch Zahlen zu einem Workload:

„360 Chunk Reads/s im Peak,
Ziel-Latenz < 80 ms,
keine Updates.“

Ohne diese Daten kannst du keine Datenbank sinnvoll auswählen.

🟩 5. Der Mini-Use-Case (zum Messen & Üben)
Bevor wir zum großen RAG-Szenario gehen, arbeitest du zuerst mit einem einfachen, kleinen Use-Case:

Drei Objekte:
Produktbeschreibung (~3 KB)

Kundenprofil (~300 Bytes)

Chatnachricht (~150 Bytes)

Drei Operationen:
Lesen

Schreiben

Append (für Chat)

Ein Mess-Setup:
Postgres

MongoDB

Mit diesen Systemen kannst du alles messen, was du brauchst.

🟧 6. Was du messen musst (Pflicht!)
Um Workloads beurteilen zu können, misst du:

Operation	MongoDB	Postgres
Read (einzeln)	X ms	Y ms
Write (einzeln)	X ms	Y ms
Update	X ms	Y ms
Append	X ms	Y ms
Bulk Read (100)	X ms	Y ms
Bulk Write (100)	X ms	Y ms
Diese 6 Messwerte ermöglichen dir später zu beurteilen:

Schafft Mongo 300 Reads/s?

Schafft Postgres 40 Updates/s?

Ist Append in Mongo schnell genug?

Ist Bulk-Ingest in Postgres zu langsam?

Die Messwerte sind nicht optional.
Sie sind die Grundlage für jede Entscheidung im Capstone-Projekt.

🟦 7. Formel: Workload = erwartete Last × gemessene Leistung
Beispiele:

Wenn du misst:
MongoDB kann 750 Reads/s

Und der Use-Case braucht:
360 Reads/s

→ passt.

Wenn du misst:
Postgres schafft 15 Writes/s

Aber dein Use-Case braucht:
40 Writes/s

→ passt nicht → Modell oder Technologie ändern (Modul 4).

Warum Workloads auch über “Cloud vs. Docker vs. Native” entscheiden
Workloads bestimmen nicht nur welche Datenbank geeignet ist,
sondern auch wie du sie betreiben kannst.

Viele Studierende (und viele Unternehmen) machen am Anfang den Fehler, einfach anzunehmen:

„Cloud ist immer besser.“

„Docker reicht für alles.“

„Lokal testen, in der Cloud betreiben.“

Das ist nicht professionell und führt oft zu Fehleinschätzungen.

Hosting hängt direkt vom Workload ab:
1. Wenn eine Datenbank für deinen Workload zu langsam ist → hilft auch Cloud nicht.
Cloud beschleunigt keine Engine, die unter deinem Workload kollabiert.
→ Erst messen, DANN über Hosting nachdenken.

2. Wenn ein Workload viele kleine Latenzen hat (<5 ms), kann Cloud zu langsam sein.
Beispiel: Redis-Sessions oder Rate-Limits
→ kleine Latenzsprünge von 2–5 ms ruinieren den kritischen Pfad.

3. Wenn ein Workload sehr I/O-lastig ist, kann Docker lokale Performance massiv reduzieren.
→ Bulk-Writes, ANN-Builds, JSONB-Indexing
→ Container-Filesysteme verhalten sich anders als native Installationen.

4. Wenn ein Workload Burst-Spitzen hat (x5/x10), sind Cloud-Preise plötzlich ein Problem.
→ Autoscaling klingt gut, wird aber teuer.

5. Wenn dein Workload klein ist, ist Cloud häufig Overkill.
→ Lokale Postgres/Redis/Mongo auf einem einzelnen Host reicht völlig.

Kurz gesagt:
Workloads verhindern Hosting-Schema-F.

Workloads zwingen dich, diese Fragen zu beantworten:

„Kann ich diesen kritischen Pfad in der Cloud-Latenz überhaupt erreichen?“

„Welche Engine verhält sich in Docker realitätsnah – welche nicht?“

„Kann ich mir Burst-Kosten für ANN-Suche leisten?“

„Reicht lokale Performance aus? Muss ich sharden?“

Erst wenn du den Workload kennst, kannst du entscheiden:

lokal

Docker

Cloud managed

hybrid

Ohne Workload → Hosting ist reine Spekulation.
Mit Workload → Hosting ist eine technisch begründete Entscheidung.


🟥 8. Übergang zum großen RAG-Use-Case
Jetzt kommen wir zurück zu unserem Customer-Service-RAG:

Du kennst aus Modul 1 die Szenarien:

Chunk Retrieval

Chat Append

Kundenprofil Update

Session Zugriff

ANN Suche

Logging

Typische Last:

12 RAG-Requests/s normal

40 RAG-Requests/s peak

Wenn jeder Request
– 6 Chunks liest
– 1 Kundenprofil liest/ändert
– 1 Nachricht anhängt
– 1 Embedding sucht

Dann ergibt sich z. B.:

Chunk Reads:
40 Requests/s × 6 Chunks = 240 Reads/s

Embedding ANN:
40 ANN-Abfragen/s

Chat-Appends:
40 Writes/s

Session State (KV):
80–120 kleine Reads/Writes/s

Ohne Workloads kannst du nicht beurteilen:

ob Mongo 240 Reads/s schafft,

ob Postgres Updates im Peak packt,

ob Redis nötig ist,

ob ANN-Suche ausgelagert werden muss.

Damit Modul 3 funktionieren kann, benötigst du diese Zahlen.

🟥 9. Capstone-Relevanz 
In deiner Abgabe musst du:

✔ für jedes Objekt ein Zugriffsszenario aus Modul 1 haben
✔ aus jedem Szenario einen Workload mit konkreten Zahlen ableiten
✔ begründen, welche Messwerte du brauchst
✔ später (in Modul 3) eine DB-Auswahl treffen
✔ zeigen, dass deine Entscheidung auf Zahlen und nicht auf Bauchgefühl basiert

Wenn du keine Zahlen angibst, kannst du keine DB begründen.

🟦 10. Mini-Aufgaben 
A) Welche Messungen fehlen?
Gegeben:
„Unser System erwartet 150 Reads/s und 30 Writes/s.“

Frage:
Welche Messungen brauchst du MINDESTENS, um zu entscheiden,
ob Postgres oder MongoDB geeignet ist?

B) Welche Aussagen sind brauchbar — welche wertlos?
„Mongo ist schneller als Postgres.“

„Mongo braucht 2,1 ms für einen Read, Postgres 4,8 ms.“

„Unsere Chats bestehen aus Anhängen, nicht Updates.“

„Unser Use-Case hat viele Reads.“

C) Baue deinen eigenen Workload
Nimm ein Objekt aus deinem Capstone (z. B. „Themenabschnitt“ oder „Beispielantwort“).

Bestimme:

Datenart

Zugriffsszenario

erwartete Häufigkeit

erwartete Parallelität

erwartete Änderungsintensität

Kritikalität

Welche Messwerte du brauchst

🟧 11. Musterlösungen 
A) Messungen, die fehlen
Read-Latenz (einzeln & bulk)

Write-Latenz (einzeln & bulk)

Update-Latenz

Append-Latenz

Durchsatz beider Systeme

Optionale p95 Latenzen

Typische Fehler:

Nur Reads gemessen

Bulk nicht gemessen

Nur eine DB getestet

Debug-Modus benutzt

Laptop im Energiesparmodus

B) Bewertung der Aussagen
Aussage	Bewertung	Warum
1	wertlos	ohne Zahlen nutzlos
2	nützlich	direkt vergleichbar
3	nützlich	beeinflusst Modell & Last
4	wertlos	keine Zahl → kein Workload
C) Beispiel-Workload
Objekt: „Themenabschnitt“
Datenart: Dokument
Zugriffsszenario: viele Reads, wenige Updates
Messwerte benötigt:

Read-Lat

Bulk-Reads

Write-Lat
DB-Kandidaten: Dokumentenspeicher

🟦 12. Check: Habe ich Modul 2 verstanden?
Kannst du:

für jedes Objekt einen Workload definieren?

Zahlen angeben statt Wörter?

die 4 Dimensionen klar anwenden?

sagen, welche Messwerte du brauchst?

erklären, warum Workloads die Vorstufe zur DB-Auswahl sind?

Wenn ja → weiter zu Modul 3: Datenbank-Auswahl auf Profi-Niveau.