Dieses Modul übersetzt die theoretischen Query Paths (Modul 4) in messbare, beweisbare Performance-Ziele und liefert die Missing Prerequisites für die Produktionsfreigabe.

1. Ziel des Moduls
Nach diesem Modul kannst du:

das P95-SLO als härtesten Constraint deines DB-Designs definieren und begründen.

das Latenz-Budget auf jeden Schritt des kritischen Pfads verteilen.

die zwei kritischsten Datenbank-Engpässe im RAG-System identifizieren und analysieren.

die Missing Prerequisites für einen Beweis der Skalierbarkeit im Capstone-Projekt erstellen.

2. Der harter Constraint: P95 Latenz-SLO
Warum 500 ms das Ziel ist (obwohl Systeme oft langsamer sind): Die Latenzen im Sekundenbereich (wie oft in der Praxis beobachtet) sind ein Zeichen für ungenügendes Engineering oder die Einhaltung eines niedrigeren SLOs. Dein Capstone muss professionelle Architektur beweisen. Das P95-Ziel von 500 ms trennt das Proof-of-Concept vom Produktions-System.

Definition des Constraints: Das Service Level Objective (SLO) ist ≤500 ms für das 95. Perzentil (P95)aller RAG-Anfragen unter Peak-Last.

Kritische Schlussfolgerung: Jede Engstelle, die unter Last mehr als ihr Budget beansprucht, führt zum Scheitern des SLO und damit zur Nicht-Produktionsfreigabe.

3. Latenz-Budget-Verteilung (Quantifizierter Critical Path)
Das 500 ms Budget muss auf die Haupt-Sektionen des Kritischen Pfads aufgeteilt werden. Die beiden fett markierten Bereiche sind die Datenbank-Engpässe, die durch dein Datenmodell (Modul 5/6) und die DB-Wahl (Modul 7) optimiert werden müssen.

Query Path Operation	Latenz-Budget (Ziel P95)	DB-Rolle	Primäres Risiko
1. Ephemeral State	≤5 ms	Redis/Cache	Blockierende Zugriffe
2. ANN-Suche (Vektor)	≤50 ms	pgvector/Vector DB	CPU-Last
3. Document Retrieval	≤60 ms	MongoDB/Document Store	Network-I/O und Locking
4. LLM-Inferenz	≤250 ms	API/GPU	Größter Single-Blocker
5. Network & Code Overhead	≤135 ms	System	Puffer für Systemschwankungen
GESAMT-BUDGET	≤500 ms	SLO-Ziel	
4. Analyse der zwei kritischen DB-Engpässe
Um die Skalierbarkeit zu beweisen, müssen Sie für mindestens einen der folgenden Engpässe die Messung und den P95-Nachweis im Capstone erbringen.

Engpass 1: Vektor-Index-Tuning (ANN Search)
Risiko: Die Approximate Nearest Neighbor (ANN)-Suche ist CPU-intensiv. Unter Peak-Last kann die Latenz schnell von 50 ms auf 200 ms steigen, wenn der Vektor-Index nicht korrekt konfiguriert ist.

Messgröße (Pflicht): Latenz der ANN-Abfrage in Abhängigkeit von Concurrent (***) Queries und den Hierarchical Navigable Small Worlds HNSW-Index-Parametern (z.B. M, ef). https://www.pinecone.io/learn/series/faiss/hnsw/

Missing Prerequisite: Der Beweis, dass das Index-Tuning (Modul 7) das 50 ms Budget unter Peak-Load einhält.

Engpass 2: Concurrent (***) Document Lookup (Chunk Retrieval)
Risiko: Das RAG-System fragt oft 6−8 Chunks pro Anfrage ab. Bei 50 gleichzeitigen Benutzern führt dies zu 300−400 punktuellen Reads/s im Document Store (z.B. MongoDB). Diese Last kann zu I/O-Überlastung oder Locking-Konflikten führen, wenn die Chunks zu groß sind (Modul 5/6).

Messgröße (Pflicht): Latenz der Multi-Chunk-Lookup-Abfrage (z.B. db.chunks.find({chunk_id: {$in: [...]}}) in Abhängigkeit von Concurrent Queries.

Missing Prerequisite: Der Beweis, dass das Small Document-Modell (Modul 5/6) und die Index-Optimierungdie 60 ms Budget unter Peak-Load einhalten.

5. Capstone-Verpflichtungen (Prüfrelevant)
Um die Missing Prerequisites zu erfüllen und die Produktionsfreigabe zu erhalten, musst du folgende Punkte explizit dokumentieren und beweisen:

SLO-Definition: Definiere das P95-SLO (500 ms) und die Begründung, warum dein System dieses Ziel anstrebt.

Budget-Zuordnung: Präsentiere die Latenz-Budget-Tabelle und erkläre, welche Maßnahme (z.B. Reference-Modell) welches Budget (60 ms) stützt.

Load-Test-Setup: Definiere das Last-Szenario (z.B. 50 Concurrent Users) und wähle das Last-Tool(Praxismodul 4.5).

Beweis eines Engpasses: Wähle einen der beiden kritischen Engpässe und liefere:

Messung: Die P95-Latenz der kritischen Operation (z.B. ANN-Search) unter Peak-Load.

Analyse: Ein Vergleich der gemessenen P95-Latenz mit dem zugewiesenen Latenz-Budget (≤50 ms).

Fazit: Begründung, ob der Critical Path für die Produktion geeignet ist.

(Die detaillierten Schritte zum Aufbau des Load-Tests folgen im Praxismodul 4.5.)

6. Quick-Check – Prüfe dein Verständnis
Kannst du:

erklären, warum die Messung des P95 wichtiger ist als der Average für die Produktionsfreigabe?

das Latenz-Budget für die ANN-Suche (50 ms) begründen?

erklären, wie der Small Document-Ansatz (Modul 5/6) die Latenz im Engpass 2 reduziert?

erklären, warum das Testen unter paralleler Last wichtiger ist als Einzel-Tests?

Wenn ja → weiter zu Modul 5: Datenmodellierung folgt Access Paths.