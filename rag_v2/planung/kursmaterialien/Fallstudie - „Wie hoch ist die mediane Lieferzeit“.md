Diese Fallstudie zeigt Dir Schritt für Schritt, wie du eine scheinbar harmlose Frage („Wie hoch ist die mediane Lieferzeit?“) vollständig  analysierst – genauso wie in deiner Capstone-Abgabe.

Der Median ist nicht trivial:
Er hängt von Frequenz, Latenz, Population, Slice, Datenmodell, Workload und Query Paths ab.

Du lernst hier:

wie du Datenarten sauber identifizierst (Modul 1)

wie du Workloads quantifizierst (Modul 2)

wie du DB-Engines auswählst (Modul 3)

wie du Query Paths analysierst (Modul 4)

Am Ende steht ein voll durchargumentiertes Beispiel, das du als Strukturgrundlage für dein Capstone verwenden kannst.

MODUL 1 — Datenarten | Zugriffsmuster | Zugriffsszenarien
Wir arbeiten strikt entlang der Checkliste.

✔ Modul-1-Checkliste: „Alle Datenarten korrekt identifiziert“
Für die Frage „Wie hoch ist die mediane Lieferzeit?“ benötigen wir folgende Datenobjekte:

Objekt A — Bestellung
Datenart: strukturiert

Felder: order_id, customer_id, product_id, order_date, shipping_date, delivery_date

Warum? Der Median entsteht aus vielen einzelnen Lieferzeiten.

Objekt B — Lieferzeit (berechnetes Feld)
Datenart: ephemeral (berechnet, nicht persistent)

Warum? delivery_date – order_date wird bei jeder Berechnung neu erzeugt.

Objekt C — Aggregierte Statistik (Median-Wert)
Datenart: kleines persistentes Objekt

Warum? Optional persistent, wenn Memoization oder Materialized View genutzt wird.

Objekt D — Filter/Slice-Parameter
Datenart: kleines JSON / Parameterobjekt

Warum? Median variiert je Produkt, Lieferant, Region usw.

✔ Modul-1-Checkliste: „Zu jedem Objekt das passende Zugriffsmuster festgelegt“
Objekt	Zugriffsmuster	Warum?
Bestellung	Read/Write mixed	es gibt neue Orders + Korrekturen
Lieferzeit	read-heavy bulk	wird bei Median-Abfrage über viele Zeilen berechnet
Median-Wert	read-heavy, selten write	lesen oft, aktualisieren selten
Slice-Parameter	read-only	wird nur als Filter genutzt
✔ Modul-1-Checkliste: „Für jedes Objekt ein Zugriffsszenario formuliert“
Objekt A — Bestellung
„Lese alle Bestellungen (ggf. per Slice) und extrahiere order_date & delivery_date.“

Objekt B — Lieferzeit
„Berechne für jede Bestellung die Lieferzeit (delivery_date − order_date).“

Objekt C — Median-Wert
„Lese die voraggregierte Statistik aus MV oder Tabelle.“

Objekt D — Slice-Parameter
„Wende Filter (WHERE product_id=… / region=…) an.“

✔ Modul-1-Checkliste: „Saubere Trennung (Dokument/Vektor etc.)“
Keine Vektoren → irrelevant

Kein Ephemeral-State außer der Lieferzeit → sauber getrennt

Bestellung persistent, Lieferzeit ephemeral

Median persistent (bei Precompute)

━━━━━━━━━━━━━━━━━━
🟠 MODUL 2 — Workloads definieren
Jetzt wird jeder Punkt der Checkliste abgearbeitet.

✔ Modul-2-Checkliste: „Für jedes Objekt ein Zugriffsszenario aus Modul 1“
Dies haben wir oben — wir übernehmen sie unverändert als Basis.

✔ Modul-2-Checkliste: „Aus jedem Szenario einen Workload mit konkreten Zahlen ableiten“
Wir definieren realistische Mengen:

Systemdaten
12.000 Bestellungen pro Tag

Median-Abfrage: 300 Anfragen / Stunde

Peak: 600 Median-Abfragen / Stunde

Workloads je Objekt
Objekt A – Bestellung
Reads/s: ~3.3

Writes/s: ~0.1

Parallelität: mittel

Kritikalität: hoch (Konsistenz!)

Objekt B – Lieferzeit (berechnet)
pro Median-Abfrage:

12.000 Bestellungen lesen

12.000 Lieferzeiten berechnen

Workload:

300 Abfragen/h → jede ~12000 rows

300 * 12.000 = 3.6 Mio Berechnungen pro Stunde

Peak: 7.2 Mio/h

→ eindeutig scan-heavy + sort-heavy

Objekt C – Median-Wert
Reads: 300/h

Writes: 1 alle 5 Minuten
→ read-heavy

Objekt D – Slice-Parameter
vernachlässigbar

✔ Modul-2-Checkliste: „Begründen, welche Messwerte du brauchst“
Notwendige Messwerte:

Cost of full table scan (Zeit pro 10k, 100k Zeilen)

Cost of sort operation

Latency for WHERE-Slices (pro product_id, supplier_id etc.)

MV-refresh-Latenz

Concurrent median calculations

Ohne diese Kennzahlen ist keine Engine-Wahl möglich.

✔ Modul-2-Checkliste: „Zeigen, dass deine Entscheidung auf Zahlen basiert“
→ wir vergleichen später mit konkreten Postgres-Messwerten
(z. B. 5–20 ms pro 10k Zeilen via Index, 50–80 ms für sortierten Slice).

━━━━━━━━━━━━━━━━━━
🟡 MODUL 3 — DB-Auswahl anhand der sechs Profi-Kriterien
Jetzt arbeiten wir alle Checklistenpunkte ab.

✔ Modul-3-Checkliste: „Datenobjekte definieren“
→ bereits in Modul 1 sauber erledigt.

✔ Modul-3-Checkliste: „Zugriffsszenarien bestimmen“
→ bereits definiert:

Bulk-Scan

Slice-Sort

MV-Read

MV-Refresh

✔ Modul-3-Checkliste: „Workloads quantifizieren“
→ haben wir in Modul 2 mit konkreten Zahlen getan (3.6 Mio Berechnungen/h).

✔ Modul-3-Checkliste: „Messwerte anwenden“
Beispielhafte realistische Werte (Postgres):

Full Table Scan 12.000 rows: 6–12 ms

Sort 12.000 numeric values: 5–8 ms

MV-Read: <2 ms

MV-refresh: 20–40 ms (async)

Mongo-typische Werte:

Sort über 12.000 Dokumente: 40–120 ms

Scan via Aggregation: 20–60 ms
→ riskant

Redis:

keine Sortierabfragen → ungeeignet

✔ Modul-3-Checkliste: „Die sechs Kriterien nutzen“
Kriterium 1 — Konsistenz
Bestellungen brauchen ACID
→ Postgres Pflicht

Kriterium 2 — Workload-Form
Scan-heavy, sort-heavy
→ Postgres stark
→ Mongo schwach

Kriterium 3 — Lastprofil
300 Median-Abfragen/h
→ Sort pro Anfrage? → zu teuer
→ MV oder Precompute nötig

Kriterium 4 — Kritische Query Paths
Median liegt im CRITICAL PATH → muss optimiert werden.

Kriterium 5 — Modellrisiko
Mongo Aggregation-Framework ineffizient bei Sort
→ großes Risiko

Kriterium 6 — Operability
Postgres: MV, Indexing, ACID → stabil
Mongo: keine MV
Redis: ungeeignet

✔ Modul-3-Checkliste: „Alternativen ausschließen“
MongoDB: teuer bei sort-heavy + kein MV → ausgeschlossen

Redis: ungeeignet für Sort → ausgeschlossen

Elasticsearch: teuer für median aggregation → oversized

✔ Modul-3-Checkliste: „Finale Entscheidung begründen“
Gewinner: Postgres
mit

einer Tabelle „orders“

einer MV „delivery_times“

Index auf product_id, region

regelmäßiger MV-Refresh

━━━━━━━━━━━━━━━━━━
🟢 MODUL 4 — Query Paths bestimmen, kritische Pfade markieren
Auch hier arbeiten wir die Checkliste streng ab.

✔ Modul-4-Checkliste: „Welche Query Paths hat dein System?“
Path A — Median „on demand“ (schlechte Variante)
Read orders (12.000 rows)

Berechne Lieferzeit

Sortiere alle Werte

Berechne Median

Antwort zurück

→ teuer, blockierend, schlecht skalierbar

Path B — Median über Materialized View (professionelle Variante)
MV lesen (indexiert, klein)

minimaler Sort

Median lesen
→ VERY LOW LATENCY (<20 ms)

Path C — MV-Refresh (asynchron)
scan new orders

berechne Lieferzeiten

update MV
→ nicht kritisch

✔ Modul-4-Checkliste: „Welche davon sind kritisch?“
Kritisch:

Path B (Median lesen)

Nicht kritisch:

Path C (MV refresh)

Bestellungs-Write

Logging

✔ Modul-4-Checkliste: „Welche Datenbanken sind involviert?“
Postgres (orders + MV)

keine weiteren Systeme

✔ Modul-4-Checkliste: „Welche Latenzanforderungen gelten?“
Median-Abfrage: < 80 ms (akzeptabel)

Ziel: < 20 ms (optimal)

MV-refresh: egal (asynchron)

✔ Modul-4-Checkliste: „Warum ist dein Modell für diese Paths optimiert?“
Weil:

MV entlastet critical path

Indexe reduzieren Sortierkosten

Postgres kann numeric sorts effizient durchführen

bulk-scan findet im background statt

Orders bleiben ACID

Roundtrips minimal (1 Query gegen MV)

✔ Modul-4-Bewertungskriterien erfüllt:
kritische Pfade korrekt erkannt → JA

Modell optimiert kritische Pfade → JA

Roundtrips vermieden → JA

DB-Wahl unterstützt Query-Pfad → JA

━━━━━━━━━━━━━━━━━━
📦 ENDGÜLTIGES ERGEBNIS 
Wenn du diese Fallstudie nachbaust, brauchst du nur die Objektbezeichnungen austauschen — Struktur und Argumentationslogik bleiben identisch.

Dieses Beispiel zeigt dir:

wie du sauber argumentierst

wie du deine Checklisten abarbeitest

wie Profi-Architektur dokumentiert wird

wie du Fehler vermeidest (Mongo für Sorts!)