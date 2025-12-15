1. Warum sich das Problem nun ändert (System-Ebene)
In den Modulen 3 bis 5 hast Du gelernt, eine einzelne Datenbank (SQL oder NoSQL) optimal für einen einzelnen, dominanten Workload zu konfigurieren und den Zugriffspfad zu optimieren.

Bisherige Annahme: Ein System = Eine DB → Lokale Optimierung.

Neue Herausforderung: Dein RAG-System besteht aus widersprüchlichen Workloads (CPU-intensive ANN-Suche und I/O-intensiver Lookup). Diese dürfen sich unter Peak-Last nicht gegenseitig blockieren, um das 500 msP95-SLO zu garantieren.

Fazit: Du wechselst von der lokalen zur systemischen Problembehandlung. Die Lösung ist die Workload-Isolation.

2. Das Kernprinzip: Workload-Isolation und Polyglot Persistence
Die Workload-Isolation ist die strategische Antwort auf die Gefahr der gegenseitigen Blockade unterschiedlicher Lastprofile.

Workload-Isolation: Die Aufteilung eines komplexen Anfragepfads in mehrere, unabhängige Sub-Workloads. Dadurch verhinderst Du, dass sich unterschiedliche Lastprofile gegenseitig negativ beeinflussen.

Polyglot Persistence: Die bewusste Entscheidung, für jeden isolierten Sub-Workload die optimal spezialisierte Datenbank-Technologie zu wählen.

Praxisfälle: Workload-Isolation in der Industrie
Workload-Typ	Primäres Problem (Engpass)	Datenbank-Strategie (Isolation)
Produktauswahl	Textsuche (hohe CPU-Last durch Index-Scans)	Elasticsearch (Isolierung auf Inverted Index)
Benutzer-Sitzungen	Gleichzeitige Lese-/Schreibzugriffe (hohe Contention, einfache Struktur)	Redis/Memcached (Isolierung auf Key-Value/In-Memory)
Transaktionshistorie	Konsistenz-Konflikte (ACID-Locking)	PostgreSQL/SQL (Isolierung der ACID-Garantie)
RAG-Retrieval	CPU-intensive Vektor-Suche (ANN)	Vektor-DB (Isolierung der HNSW-Berechnung)
3. Der Entscheidungspfad des Architekten (Beispiel RAG System)
Als Datenbank-Spezialist triffst Du Technologie-Entscheidungen nicht aus dem Bauch heraus, sondern anhand eines klaren, kriterienbasierten Pfades.

3.1. Workload-Analyse
Du wendest die Kriterien aus den Modulen 3/4/5 auf jeden Sub-Workload an, aber mit dem Fokus auf die Latenzgarantie (SLO):

RAG-Sub-Workload	Latenz-Budget	Kriterium (Lastprofil)	Ergebnis (Notwendigkeit der Isolation)
ANN-Suche	≤50 ms	CPU-intensiv(Distanzberechnung)	Muss auf dedizierte CPU-Ressourcen mit spezialisiertem Index (HNSW) isoliert werden.
Chunk-Lookup	≤60 ms	I/O-intensiv(Concurrent Lookups)	Muss auf ein System mit schnellen I/O-Operationen und sauber indexierten Key-Value-Lookups isoliert werden.
3.2. Metadaten: Der Hebel zur Latenz-Isolation
Die Metadaten sind der aktive Partitionierungs-Hebel, der Dir hilft, die Workload-Isolation zu erreichen, indem er die Last der ANN-Suche aktiv reduziert.

Strategie	Funktion	Ort der Workload-Isolation	Zweck
Pre-Filtering	Einschränkung des Suchraums (z.B. doc_id='XYZ')	Vektor-DB (Filter vor HNSW-Suche)	Sicherung der ≤50 ms durch Reduktion der CPU-Last.
Post-Filtering	Selektion und Sortierung der Top-K-Ergebnisse	Anwendungscode	Qualitätsoptimierung und logische Kohärenz.
3.3. Metadaten-Extraktion: Die fehlende Voraussetzung
Die Metadaten, die Du zum Filtern benötigst, musst Du im Ingest-Pfad erzeugen.

Implementiere die Logik, um schwache Metadaten (wie section_title oder position) aus dem Text abzuleiten (z.B. mittels unstructured.io) und sie redundant in Dein Vektor-Schema (für Pre-Filtering) und Dein Document-Schema (für Post-Filtering) zu speichern.

Starke vs. Schwache Metadaten
Die Kategorisierung hängt davon ab, ob die Daten explizit und unveränderlich im Quellsystem existieren oder ob sie heuristisch aus dem Inhalt abgeleitet werden müssen.

Kriterium	Starke Metadaten (Explizit/Zertifiziert)	Schwache Metadaten (Abgeleitet/Heuristisch)
Definition	Explizite, strukturierte Daten, die direkt und garantiert aus dem Quellsystem stammen (z.B. Dateisystem, Datenbankeintrag, API-Feld).	Implizite, unstrukturierte Daten, die aus dem Textinhalt selbst abgeleitet, extrapoliert oder geraten werden müssen.
Zuverlässigkeit	Hoch (Kann für Pre-Filtering verwendet werden).	Moderat (Eher für Post-Filtering und Qualitätsverbesserung).
Speicherort	Wird oft redundant in allen Datenbanken gespeichert.	Wird durch die Ingest-Pipeline erzeugt und gespeichert.
Beispiele	doc_id (Eindeutige ID des Dokuments), product_family (Produktfamilie), creation_date(Erstellungsdatum der Datei), author (Autor der Quelldatei).	section_title (Titel des Abschnitts, in dem der Chunk steht), position (Laufender Index des Chunks im Dokument), chunk_summary (Zusammenfassung des Chunk-Inhalts).

4. Capstone-Checkliste: Workload-Isolation und Verifikation
Diese Checkliste fasst die Schritte zusammen, die Du in Deinem Labor-Modul durchführen musst, um die architektonische Entscheidung zur Workload-Isolation zu beweisen und zu verifizieren.

Nr.	Schritt/Aktion (Datenbank-Experte)	Kriterium/Metrik	Nachweis (Labor/Dokumentation)
1.	Workload-Partitionierung. Definiere die Workloads (ANN vs. Lookup) und weise die Budgets (≤50 msvs. ≤60 ms) zu.	Anforderung: P95-Budgets für jeden Sub-Workload.	Tabelle der Latenz-Budgets.
2.	Metadaten-Implementierung. Implementiere die Logik zur Extraktion der schwachen Metadaten(z.B. section_title).	Methode: Ingest-Pipeline mit unstructured.io Logik.	Code-Ausschnitt und Schema-Erweiterung (Modul 6).
3.	Isolationstechnik definieren. Wähle die Metadaten-Felder für das Pre-Filtering des Vektor-Workloads.	Ziel: Logische Partitionierung des Suchraums.	Dokumentiertes Pre-Filtering-Schema (Vektor-DB).
4.	Concurrent Lookup prüfen. Messe die Latenz der Multi-Chunk-Lookups unter Peak-Last.	Anforderung: P95≤60 ms.	P95-Protokoll der Messung (Nachweis der I/O-Isolation).
5.	Pre-Filtering-Effekt messen. Messe die P95-Latenz der ANN-Suche einmal ohne und einmal mit Pre-Filtering-Metadaten.	Anforderung: Latenz muss durch Pre-Filtering ≤50 ms garantieren.	P95-Protokoll beider Messungen (Nachweis der CPU-Isolation).
6.	Tuning-Hebeleinsatz. Justiere den HNSW-Parameter ef und beweise, dass Du die Latenz aktiv steuern kannst.	Ziel: Finde den optimalen Trade-Off Latenz≤50 ms vs. Recall (Genauigkeit).	Dokumentation der ef-Wahl und des Recall-Verlusts.