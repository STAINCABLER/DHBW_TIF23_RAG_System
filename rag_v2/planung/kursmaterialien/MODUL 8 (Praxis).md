1. Laborziel
Nach dieser Übung kannst Du:

Die Logik zur Filter-Extraktion aus natürlicher Sprache (Query-Analyse) implementieren.

Schwache Metadaten extrahieren und Deinem Schema hinzufügen.

Den Pre-Filtering-Effekt (CPU-Isolation) und die Concurrent Lookup Latenz (I/O-Isolation) durch Messung verifizieren.

2. Phase I: Implementierung der Filter-Logik und Extraktion
Der gesamte Workload-Isolation-Ansatz scheitert, wenn der Filter nicht zuverlässig aus der Benutzeranfrage gewonnen werden kann.

Schritt 1: Query-Analyse: Filter-Extraktion aus natürlicher Sprache
Du simulierst den Query-Analyse-Agenten (ein kleines LLM oder Regelwerk), der die Benutzeranfrage in ein abfragbares JSON-Filterobjekt übersetzt.

Ziel: Implementiere eine Funktion, die eine Benutzeranfrage (string) in ein JSON-Filterobjekt umwandelt, das Deine Metadaten-Felder nutzt.

Aktion (LLM-Basiert): Nutze Dein Haupt-LLM (oder ein kleineres, schnelleres Modell) und ein System-Prompt, um es als "Filter-Extraktions-Agenten" zu instruieren.

Input: Benutzeranfrage: "Ich brauche die aktuellsten Informationen zur Produktfamilie Alpha (2024)."

Output (JSON):

JSON

{
  "product_family": "Alpha",
  "year": 2024,
  "doc_type": "current"
}
Aufgabe: Schreibe den Code, der die Ausgabe dieses JSON (deine Filter-Kriterien) als ersten Schritt im Retrieval-Pfad an die Vektor-DB zur Pre-Filterung übergibt. Dies ist der zwingende Anfang Deiner Workload-Isolation.

Schritt 2: Extraktion und Redundante Speicherung der Metadaten
Nun erzeugst Du die Filter-Daten im Ingest-Pfad.

Aktion: Erweitere Deine Ingest-Pipeline (Modul 6), um schwache Metadaten wie section_title (letzter Titel im Dokument) und position (Index des Chunks) zu extrahieren.

Redundanz: Bestätige in Deinem Code/Schema, dass:

Vektor-DB: Nur die Pre-Filter-Kriterien (doc_id, product_family, section_title) speichert.

Document-DB: Den vollen Chunk-Text und alle Metadaten (inklusive position) speichert.

Schritt 3: Implementierung des Hybrid-Retrieval-Orchestrators
Führe alle Schritte in einem zentralen Code-Pfad zusammen. Dieser Code ist der Beweis für Deine Polyglot-Persistence-Architektur.

Filter Extraktion: Nimm die Benutzeranfrage und erzeuge das JSON-Filterobjekt (Schritt 1).

Pre-Filtering: Schicke das JSON-Filterobjekt und das Embedding der Query an die Vektor-DB.

ANN-Suche: Führe die HNSW−Suche nur auf den gefilterten Vektoren durch.

Multi-Lookup: Nimm die chunk_ids der k=8 besten Ergebnisse.

(Optional, s.u) Concurrent I/O: Rufe die k=8 Chunks parallel (concurrently) von der Document-DB ab.

Post-Filtering: Sortiere die Ergebnisse (z.B. nach position) und übergib sie an das LLM.

4. Phase II: Verifikation der Workload-Isolation durch Messung (Schritt 4–6)
Hier misst Du die Latenz der Sub-Workloads unter realistischer Last.

Schritt 4: Nachweis der CPU-Isolation (Pre-Filtering-Effekt)
Ziel: Beweise, dass Dein Filter die CPU-Last des Vektor-Workloads so stark reduziert, dass die ≤50 ms garantiert werden.

Messung A (Worst-Case): Messe die P95-Latenz der ANN-Suche OHNE Metadaten-Filter.

Messung B (Isoliert): Messe die P95-Latenz der ANN-Suche MIT einem scharfen Filter (z.B. nach doc_id).

Bewertung: Die P95-Latenz in Messung B muss signifikant niedriger sein und Dein Budget (≤50 ms) einhalten.

OPTIONAL: Schritt 5: Nachweis der I/O-Isolation (Concurrent Document Lookup)
Ziel: Beweise, dass Dein Document Store die gleichzeitigen Lookups von 6–8 Chunks pro Nutzer unter Stress innerhalb des I/O-Budgets (≤60 ms) verarbeiten kann.

Load-Tool Setup (WIE):

Simulierte Last: Simuliere 50 bis 100 gleichzeitige Benutzeranfragen (Threads/Prozesse). Dies entspricht Deiner Peak-Last.

Lookup-Szenario (WAS): Jede der 50 simulierten Anfragen MUSS eine parallele (concurrent) Datenbankabfrage starten, um 8 zufällige $\mathbf{chunk_id}$s von der Document-DB abzurufen.

Wo Concurrency zählt: Die gleichzeitigen (parallelisierten) I/O-Zugriffe von allen 50 Nutzern sind das Nadelöhr, das Du testest.

Bewertung (WANN/WAS):

Messe die P95-Latenz des gesamten Multi-Lookups (von Abfragebeginn bis zum letzten abgerufenen Chunk).

Die P95-Latenz MUSS ≤60 ms sein.

Schritt 6: Tuning und Trade-Off Beweis
Führe das Experiment zur HNSW-Index-Optimierung durch.

Aktion: Variiere den HNSW−Parameter ef und messe jedes Mal die Latenz (P95) und den Recall.

Entscheidung: Wähle den kleinsten ef-Wert, der die P95-Latenz ≤50 ms garantiert. Dokumentiere, warum Du den möglichen Recall-Verlust an dieser Stelle akzeptierst.

5. Capstone-Checkliste (Praxismodul 8)
Status	Aufgabe (Must-Have)	Nachweis in der Dokumentation
☐	Query-Analyse implementiert: Die Logik zur Generierung von JSON-Filternaus der Benutzeranfrage ist funktionsfähig.	Code-Ausschnitt des Filter-Extraktions-Agenten.
☐	Metadaten Extraktion: Die Logik zur Ableitung von schwachen Metadaten(section_title / position) ist in der Ingest-Pipeline implementiert.	Code-Ausschnitt der Metadaten-Extraktionslogik.
☐	CPU-Isolation Bewiesen: Die P95-Latenz der ANN-Suche mit Pre-Filter ist gemessen und bestätigt die ≤50 ms Garantie.	P95-Protokoll der Messung (Nachweis der CPU-Isolierung).
☐	I/O-Isolation Bewiesen: Die P95-Latenz des Concurrent Multi-Lookups(Schritt 5) ist gemessen und bestätigt die ≤60 ms Garantie unter Peak-Last.	P95-Protokoll der Concurrent-Lookup-Messung.
☐	Index-Tuning-Entscheidung: Der gewählte HNSW-Parameter (ef) ist begründet durch den gemessenen Trade-Off (Latenz vs. Recall).	Dokumentation der ef-Wahl und des Recall-Verlusts.



Optionaler Exkurs: Concurrency verstehen (I/O-Isolation)
Das kritische I/O-Budget von ≤60 ms für den Multi-Lookup erfordert asynchrone Programmierung.

Was ist Concurrency und warum ist sie nötig?
Dein Datenbank-Lookup ist eine I/O-gebundene Operation. Dein Code muss auf die Netzwerk- und Festplattenlatenzder MongoDB warten.

Serielle Ausführung: Die I/O-Wartezeiten von 8 Anfragen addieren sich unnötig auf.

Asynchrone Concurrency: Dein Code sendet alle 8 Abfragen gleichzeitig an die Datenbank. Während der Code auf die I/O-Antwort von Anfrage 1 wartet, nutzt er die Zeit, um die Anfragen 2 bis 8 zu managen und zu starten.

Resultat: Die 8 I/O-Wartezeiten überlappen sich. Die Gesamtlatenz des 8−fach−Lookups reduziert sich drastisch.

Vertiefung: Für eine detailliertere Erklärung der asynchronen I/O-Mechanismen und deren Implementierung (z.B. in Python mit asyncio.gather), siehe diesen Artikel:

https://realpython.com/async-io-python/#a-first-look-at-async-io

Implementierungshinweis für den Lookup
Stelle sicher, dass Dein Datenbank-Treiber (z.B. motor für MongoDB) die asynchrone $in Query oder die gleichzeitigeAusführung von 8 find_one-Aufrufen unterstützt, um diesen Vorteil zu nutzen.

