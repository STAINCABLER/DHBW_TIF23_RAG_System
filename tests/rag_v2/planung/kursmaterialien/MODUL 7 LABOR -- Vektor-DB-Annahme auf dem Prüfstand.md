Dieses Modul ist die Laboraufgabe zur Verifizierung der Annahmen aus Modul 7. Du sollst überprüfen, ob die Workload-Trennung für Deinen Anwendungsfall zwingend notwendig ist, um das 500 ms P95-SLO einzuhalten.

1. Ziel der Laboraufgabe
Nach dieser Übung kannst Du:

die 50 ms Latenz-Anforderung an die ANN-Suche unter Last messen und bewerten.

beweisen, ob die Workload-Trennung (dedizierte Vektor-DB) für Deine Datenmenge nötig ist.

den Latenz-Trade-Off Deines Vektor-Indexes (HNSW) aktiv steuern.

2. Hypothese zur Überprüfung (Modul 7)
Hypothese: Die ANN-Suche ist so CPU-intensiv, dass sie in der gleichen Datenbank-Instanz wie die kritischen Chunk-Lookups das 500 ms P95-SLO des Gesamtsystems reißt. Daher ist eine dedizierte Vektor-DB zwingend nötig.

Deine Aufgabe: Finde heraus, ob Du diese Hypothese für Deine Datenmenge (Modul 2) widerlegen kannst.

3. Setup und Vorbereitung
Vektor-Datensatz: Verwende den in Modul 6 erstellten Chunk-Datensatz. Erstelle die Embeddings dafür (z.B. mit all-MiniLM-L6-v2, 384 Dimensionen).

Load-Tool: Nutze Dein gewähltes Last-Tool (Modul 4.5) zur Simulation des Peak-Loads (z.B. 50 Concurrent Users).

Testumgebungen: Du benötigst zwei Umgebungen für den Vergleich:

Test A (Integrierte DB): Deine MongoDB-Instanz, in der Du die Vektoren zusätzlich speicherst (z.B. als Array im Chunk-Dokument oder in einer eigenen Collection).

Test B (Polyglott/Dediziert): Deine dedizierte Vektor-DB (z.B. pgvector oder Mongo Atlas Vector Search).

4. Kritische Mess-Szenarien und Metriken
Du musst die P95-Latenz der kritischsten Operation messen: der ANN-Suche (≤50 ms Budget).

A. Messung 1: Worst-Case ANN-Search Latenz (Beweis der Ineffizienz)
Ziel: Messe, wie schnell eine Suche ohne optimierten Index (oder auf einer ineffizienten Umgebung) ist.

Szenario	Metrik	Test-Setup (Hypothese)
P95-Latenz (Unoptimiert)	Zeit für 5 Vektor-Abfragen ohne Metadatenfilter unter Peak-Last.	Test A (MongoDB ohne Vektor-Index, oder Full Table Scan):Wie schnell ist die Suche ohne Optimierung?
Erwartung: Dieser Wert wird deutlich über 50 ms liegen und wahrscheinlich das gesamte 500 ms SLO der Anfrage reißen.

B. Messung 2: P95 Latenz mit Dedizierter Optimierung (Beweis der Notwendigkeit)
Ziel: Zeige, dass die ≤50 ms nur durch den spezialisierten Index erreicht werden.

Szenario	Metrik	Test-Setup (Beweis)
P95-Latenz (HNSW/Optimiert)	Zeit für 5 Vektor-Abfragen mit Metadatenfilter unter Peak-Last.	Test B (pgvector/Dedizierte Vektor-DB): Messung der Latenz mit aktivem HNSW-Index.
Nachweis: Die gemessene P95-Latenz MUSS ≤50 ms sein.

C. Messung 3: Latenz-Trade-Off (Index-Tuning)
Ziel: Beweise, dass Du den Index aktiv steuern kannst.

Experiment: Führe die Messung 2B dreimal durch und variiere den HNSW-Parameter ef (Such-Effizienz) im Vektor-Index:

Lauf 1: Niedriges ef (Schnell, ungenau)

Lauf 2: Moderates ef

Lauf 3: Hohes ef (Genau, langsam)

Messung: Trage die P95-Latenz gegen den Recall (Genauigkeit der Top-5-Ergebnisse) auf.

Ergebnis: Du musst den optimalen Punkt finden, der ≤50 ms garantiert, ohne die Genauigkeit zu stark zu opfern.

5. Kurzbegründung (Nach der Messung)
Du schließt die Laboraufgabe ab, indem Du folgende Fragen beantwortest:

War die Hypothese von Modul 7 richtig? Konnte die ineffiziente Umgebung (Test A) das 50 ms Budget einhalten? Wenn ja: Warum? (Wenig Daten? Extrem gute Metadaten?)

Welchen ef-Wert hast Du gewählt, um die ≤50 ms Latenz zu garantieren, und welchen Trade-Off(Genauigkeitsverlust) bedeutet das?

6. Capstone-Checkliste (Modul 7)
Um die Eignung Deines Vektor-Modells zu beweisen, musst Du diese Ergebnisse in Deiner Dokumentation enthalten:

✔ Latenz-Beweis: Protokoll der P95-Messung der ANN-Suche unter Peak-Load.

✔ Budget-Einhaltung: Nachweis, dass Dein gewähltes Setup (Test B) das ≤50 ms Budget einhält.

✔ Index-Tuning-Entscheidung: Dokumentation des gewählten HNSW-Parameters (z.B. ef=15) und Begründung des damit verbundenen Recall vs. Latenz-Trade-Offs.