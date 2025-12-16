# ABSCHLUSSMODUL - Vom Prototyp zur Produktionsreife

## 1. Einleitung: Die Architektonische Entscheidungskaskade

Wir haben in Modul 8 die Notwendigkeit der Workload-Isolation und Polyglot Persistence kennengelernt. Das ist die Zielarchitektur. Bevor man diese Komplexität jedoch implementiert, muss man sich als Data Engineer fragen: Ist der Aufwand gerechtfertigt?

In der Praxis folgen Entscheidungen einer klaren Kaskade der Komplexität.

### A: Polyglot Persistence – Der vollständige Rationale

Die moderne RAG-Architektur besteht im Vollbetrieb oft aus mindestens drei spezialisierten Datenbank-Systemen. Jede Technologie isoliert einen kritischen Workload, um das P95−SLO (Modul 4) zu garantieren.

| Technologie | Workload (Primäre Last) | Latenz-Anforderung | Warum Polyglot (Rolle) |
|-------------|-------------------------|-------------------|------------------------|
| Document/RDBMS | Dokument-Speicher, Kontext-Lookup (I/O) | ≤60 ms | Speichert den vollständigen Chunk-Text und die starken/schwachen Metadaten als I/O-isolierte Einheit. |
| Vector DB | Ähnlichkeitssuche (CPU) | ≤50 ms | Speichert die Embeddings und Pre-Filter-Metadaten als CPU-isolierte Einheit. |
| Key-Value Store (z.B. Redis) | Session-Management, Rate Limiting, Caching | ≪5 ms | Speichert temporäre, extrem latenzkritische Daten (z.B. Benutzer-Sitzungen oder Filter-Caches) als extrem I/O-isolierte Einheit. |

### B: Einfachheit schlägt Komplexität – Der Wenn-Dann-Pfad

Die größte Gefahr im Prototyping ist die Über-Optimierung. Jede zusätzliche Datenbank erhöht die Operationale Komplexität (Wartung, Backup, Consistency). Du darfst nur dann die Komplexität erhöhen, wenn der vorherige, einfachere Ansatz gescheitert ist.

**Der Entscheidungspfad zur Komplexitätserhöhung:**

| Entscheidung (Wenn...) | Maßnahme (Dann...) | Begründung (Warum?) |
|------------------------|-------------------|---------------------|
| Wenn der lokale Access Path (M5) einer Single-DB (z.B. nur pgvector) das SLO einhält... | Dann wähle die einfachste Single-DB-Lösung. | Die Komplexität des Betriebs ist minimal. "Keep it Simple." |
| Wenn die Latenz des Multi-Lookups (M8) unter Peak-Last das ≤60 ms I/O-Budget reißt... | Dann implementiere die Workload-Isolation auf Document/Vector (Zwei-DB-Architektur). | Die I/O-Contention kann nur durch Aufteilung der Last auf spezialisierte Systeme gelöst werden. |
| Wenn der Session-Management-Workload (Benutzer-Logins, Rate-Limit-Check) das P95-SLO des gesamten Backends reißt... | Dann implementiere den Key-Value Store zur Isolierung dieses extrem latenzkritischen Workloads. | Der KV-Store ist der letzte Schritt der Isolation. Er dient der Systemstabilität, nicht primär der RAG-Qualität. |

### C: Data Engineering = Dokumentierte Entscheidungen

Der Capstone-Report dient nicht dazu, das Ergebnis zu präsentieren, sondern den Entscheidungsprozess zu dokumentieren. Nur wenn Du Deine Entscheidungen begründen kannst, hast Du den Kurs verstanden.

**Die 4 Säulen des Capstone-Nachweises:**

Dein Capstone-Report muss/kann/darf/sollte;-) für jede wichtige architektonische Entscheidung (DB-Wahl, Metadaten-Nutzung, Tuning) die folgenden vier Fragen beantworten:

| Säule | Beschreibung | Beispiel |
|-------|--------------|----------|
| 1. Begründung | Welches Problem löst diese Entscheidung, basierend auf dem Workload? | Problem: ANN-Suche ist CPU-gebunden und reißt das ≤50 ms Budget. Lösung: Wahl einer Vektor-DB. |
| 2. Alternative | Welche anderen Technologien oder Tuning-Hebel wurden ausgeschlossen und warum? | Alternative: pgvector als Single-DB. Ausschluss: Ab 10 Mio Vektoren wird das Tuning zu aufwendig/teuer. |
| 3. Nachweis (Beweis) | Welcher Messwert beweist, dass die Entscheidung die Anforderung erfüllt? | Der P95-Latenztest (M8, Schritt 4) beweist, dass das Pre-Filtering die ≤50 ms CPU-Isolation garantiert. |
| 4. Risiko | Welche neue Komplexität oder welcher Trade-Off entsteht durch diese Entscheidung? | Risiko: Einführung von Polyglot Persistence erhöht die betriebliche Komplexität (Backups, Consistency). Trade-Off: HNSW-Tuning führt zu einem Recall-Verlust (Modul 7/8). |

---

## Worked Example

### Szenario und Zielsetzung (Der Rote Faden: Zugriffsszenario)

Ein mittelständischer Softwarehersteller möchte die Effizienz seines technischen Supports steigern, indem er ein KI-Portal einführt, das auf der Wissensbasis des Unternehmens basiert.

| Stakeholder / Zugriffsszenario | Ziel | SLO (Latenz-Anforderung) |
|--------------------------------|------|--------------------------|
| Endkunde (Self-Service) | Schnelle Antwort auf Standardfragen (z.B. Installationsfehler). | P95 ≤1.5 Sekunden (akzeptabel für Chat-Antwort). |
| Service-Mitarbeiter (Agent-Assist) | Sofortiger Abruf von Kontextwissen für Live-Gespräche. | P95 ≤500 ms (kritisch, da Verzögerung im Live-Gespräch stört). |

## 2. Architektonische Annahmen und Datenbasis

Die Heterogenität der Daten (unterschiedliche Frequenzen und Formate) macht die Polyglot Persistence zur Notwendigkeit.

### A. Datenquellen und Update-Frequenz (Wichtig für das Schema)

| Daten-Typ | Primäres Format (Ursprung) | Update-Frequenz | Rolle (Wichtig für Latenz/Filter) |
|-----------|---------------------------|-----------------|-----------------------------------|
| Handbücher/Doks | PDFs, MS Word | Qartalsweise (gering) | Statische Wissensbasis. Ideal für Vektor- und Document Store. |
| Kundendaten/Verträge | RDBMS (z.B. CRM-System) | Stündlich/Live | Starke Metadaten. Muss live in den Query-Path integriert werden. |
| Chat-Historien | JSON/BSON-Dokumente | Echtzeit | Dynamischer I/O-Workload (Hohe Schreiblast und Lesezugriff). |

### B. Last- und Performance-Annahmen

| Kriterium | Agent-Assist (Service-Mitarbeiter) | Self-Service (Endkunde) |
|-----------|-----------------------------------|-------------------------|
| Gleichzeitige User | 150 gleichzeitige Sessions (Druck auf I/O und Filter). | 1.000 Requests/Stunde (Druck auf CPU-Suche). |
| Zugriffsmuster | Gezielt, kontextuell. Fragen beinhalten oft die Ticket-ID. | Ad-hoc, generisch. Oft weiche, ungenaue Fragen. |

## 3. Workload-Analyse und Workload-Isolation (Modul 3 & 8)

Wir konzentrieren uns auf den kritischsten Workload (≤500 ms SLO) und leiten die technischen Profile ab.

### 3.1. Ableitung des Workload-Profils (Der Plausible Übergang)

❓ Wie leitet man das Workload-Profil ab? Man übersetzt die SLO-Anforderung und die Geschäftslogik (Zugriffsszenario) in ein Last-Risiko für die Datenbank.

| Zugriffsszenario | Geschäftslogik / Last-Risiko | Abgeleitetes Workload-Profil |
|------------------|------------------------------|------------------------------|
| A. Agent-Assist (≤500 ms SLO) | Risiko: Die Suche muss extrem gezielt sein (Filter-Pflicht). Jede Millisekunde zählt. | Kritischer, Hybrid-Workload: Benötigt massive Filter-Last (CPU-Filterung) gefolgt von Multi-I/O-Lookups. |
| B. Endkunde (≤1.5 s SLO) | Risiko: Suche ist generisch, kein scharfer Filter möglich. | CPU-Intensiver Workload: Hohe ANN-Suchlast über den gesamten Vektor-Raum. Latenz toleriert, aber Recall muss hoch sein. |

### 3.2. Workload-Zerlegung und Latenzbudgets

Der kritische Agent-Assist-Workload wird in isolierbare Sub-Workloads zerlegt:

| Sub-Workload | Lastprofil | Latenz-Budget | Isolationstechnik |
|--------------|------------|---------------|-------------------|
| 1. Query-Analyse | Mustererkennung (Light CPU) | ≤50 ms | Rule-Engine (Extrahiert starke Metadaten). |
| 2. ANN-Suche | CPU-Intensiv (Distance) | ≤50 ms | Vektor-DB (Isolierung der CPU-Last). |
| 3. Chunk Retrieval | I/O-Intensiv (Lookups) | ≤60 ms | Document Store (Isolierung der I/O-Last). |
| 4. LLM-Generation | Inferenz (Kritische CPU) | ≤250 ms | Dedizierte Hardware (Außerhalb der DB). |

## 4. Query-Path und Access-Path (Modul 5 & 8)

Wir betrachten, wie der Agent-Assist-Workload technisch umgesetzt und abgesichert wird.

### 4.1. Der Query-Path des Agenten (Der Orchestrator)

📘 **Konzept-Abgrenzung:**

- **Query-Path:** Beschreibt die logische Abfolge der Abfragen über mehrere Services/Datenbanken hinweg (Der "Orchestrator-Fluss").
- **NICHT Access-Path:** Der Query-Path ist der übergeordnete Ablauf, bevor eine einzelne Datenbank vom Access-Path optimiert wird.

**Beispiel:** Mitarbeiter fragt: "Finde die Lösung für Ticket T−4567."

1. Start: Orchestrator empfängt die Anfrage.
2. Filter-Extraktion: Analyse erkennt T−4567 (Starkes Metadatum).
3. CRM-Lookup: Orchestrator fragt die Kundendaten-DB live ab (welche Module, Verträge).
4. Pre-Filtering: Vektor-DB-Abfrage initiiert MIT T−4567 und Modul_ID als starke Filter.
5. Concurrent Retrieval: Die k besten IDs werden asynchron vom Document Store abgerufen.

### 4.2. Access-Path der Vektor-DB (SLO-Sicherung)

📘 **Konzept-Abgrenzung:**

- **Access-Path:** Beschreibt, wie eine spezifische Datenbank die Anfrage technisch verarbeitet und welche Indexe sie nutzt.
- **NICHT Workload:** Der Access-Path ist die spezifische Implementierung (Index-Auswahl) zur Bewältigung des Workloads.

**Metadaten-Strategie:** Der Access-Path nutzt den starken Metadaten-Index (ticket_id) zur logischen Partitionierung des Vektor-Raums, um die 50 ms Latenz zu garantieren.

**Tuning:** Der ef-Parameter wird gegen die Latenz gemessen (Trade-Off: Latenz vs. Recall).

### 4.3. Access-Path der Document-DB (I/O-Isolation)

**Metadaten-Strategie:** Der Access-Path nutzt einen Compound Index auf doc_id und chunk_id.

**Tuning:** Wir nutzen asynchrone Code-Logik (Concurrency, Modul 8) auf der Anwendungsschicht, um die I/O-Wartezeiten zu überlappen und das ≤60 ms Budget zu garantieren.

## 5. Architektonischer Abschluss und Dokumentation

### A. Die 3-Speicher-Architektur (Rolle des KV-Stores)

| DB-Technologie | Isolierter Workload | Rolle für die Latenzsicherung |
|----------------|--------------------|-----------------------------|
| Document/RDBMS | Dokument-Speicher / Chunk Lookup | Sichert I/O-Last (≤60 ms). |
| Vector DB | Ähnlichkeitssuche / ANN-Filterung | Sichert CPU-Last (≤50 ms). |
| Key-Value Store (Redis) | Session-Management, Filter-Caching | Sichert Systemstabilität (≪5 ms) und hält latenzkritische Sessions/Locks. |

### B. Nachweis (Capstone-relevant)

Ihr müsst/dürft/könnte im Capstone-Report die Begründung der architektonischen Entscheidungen gemäß der vier Säulen dokumentieren:

| Säule | Anwendung in dieser Case Study |
|-------|--------------------------------|
| 1. Begründung | Die Polyglot-Architektur ist notwendig, da die Lastprofile (CPU-Last und I/O-Last) unterschiedliche SLOs haben und sich bei einem Single-DB-Setup gegenseitig ausschließen (Workload-Isolation). |
| 2. Alternative | Eine Single-DB-Lösung (z.B. pgvector) wurde ausgeschlossen, da sie unter der kombinierten Peak-Last der 150 Agenten + 1.000 Endkunden das ≤500 ms SLO des Agenten-Workloads nicht garantieren kann. |
| 3. Nachweis | Der P95-Latenztest (M8) beweist, dass der Pre-Filter auf ticket_id die ≤50 ms CPU-Isolation garantiert, und die Concurrent Lookups die ≤60 ms I/O-Isolation. |
| 4. Risiko | Hohe Betriebskomplexität durch drei Datenbanken; Risiko der Datenkonsistenz zwischen dem Live-CRM und den archivierten Daten. |

---

## Musterantworten für den Capstone-Nachweis (Szenario: Agent-Assist)

Die folgenden Antworten dienen als Rahmen, um die Architekturentscheidungen für das P95≤500 ms SLO des Service-Mitarbeiter-Workloads zu dokumentieren.

### 1. Begründung: Welches Problem löst diese Entscheidung?

Die Entscheidung für die Polyglot Persistence (Vector DB + Document DB) löst das Problem der Ressourcenkonkurrenz unter Peak-Last (Concurrent Users).

Obwohl die Prozesse seriell ablaufen (zuerst ANN, dann Chunk Retrieval), teilen sie sich in einem Single-DB-System dieselbe CPU und denselben I/O-Kanal.

**Das Problem:** Bei 150 gleichzeitigen Agent-Assist-Anfragen wird die I/O-intensive Lese-Last (Holen der Chunks aus dem Speicher) der ersten Anfragen die CPU-intensive Index-Berechnung (ANN-Suche) der nachfolgenden Anfragen durch I/O-Wartezeiten blockieren.

**Die Lösung:** Wir isolieren den CPU-Workload (ANN-Suche, Budget ≤50 ms) auf die Vektor-DB und den I/O-Workload (Chunk-Lookup, Budget ≤60 ms) auf den Document Store. Dies verhindert, dass sich unterschiedliche Lastprofile um dieselbe kritische Ressource streiten und garantiert die Workload-Isolation.

### 2. Alternative: Welche Alternativen wurden ausgeschlossen und warum?

Die primäre Alternative war die Nutzung einer Single-DB-Lösung (z.B. pgvector oder MongoDB mit Vektor-Index) mit lokalem Tuning (Modul 5).

**Ausschlussgrund (Technisch):** Bei einem Datenvolumen von 10 Mio. Vektoren und dem SLO von ≤500 ms ist es nicht möglich, 100% zu garantieren, dass der lokale Index-Filter und das HNSW-Tuning die Latenz bei gleichzeitiger I/O-Last stabil halten. Die 50 ms für die ANN-Suche würden bei starkem I/O-Druck unvorhersehbar gerissen.

**Ausschlussgrund (Methodisch):** Die Single-DB-Lösung erzwingt einen Trade-Off zwischen der Optimierung des CPU-Workloads und des I/O-Workloads (M5), was im kritischen Agent-Assist-Szenario nicht akzeptabel ist. Die Polyglot-Architektur ermöglicht die unabhängige Optimierung beider Workloads.

### 3. Nachweis: Welcher Messwert beweist, dass die Entscheidung die Anforderung erfüllt?

Der Nachweis erfolgt durch die strikte Einhaltung der P95-Budgets für die isolierten Workloads unter Peak-Last-Bedingungen (150 gleichzeitige Sessions).

**Nachweis der CPU-Isolation:** Die P95-Latenz der ANN-Suche (Vektor-DB) mit aktiviertem ticket_id-Pre-Filter (starkes Metadatum) liegt bei 38 ms. Dies beweist, dass die isolierte CPU-Last das Budget von ≤50 ms einhält und nicht durch I/O-Last beeinträchtigt wird.

**Nachweis der I/O-Isolation:** Die P95-Latenz des Concurrent Multi-Lookups (Document Store) liegt bei 55 ms. Dies beweist, dass der I/O-Workload das Budget von ≤60 ms einhält und nicht durch konkurrierende CPU-Last blockiert wird.

### 4. Risiko: Welche neue Komplexität oder welcher Trade-Off entsteht?

Die Einführung der Polyglot-Architektur schafft neue Risiken und erfordert bewusste Trade-Offs:

**Komplexität (Operational):** Erhöhte Betriebskomplexität durch die Wartung, das Monitoring und das Patching von drei unterschiedlichen Datenbank-Systemen (Vector, Document, KV).

**Risiko (Konsistenz):** Es besteht das Risiko der Dateninkonsistenz zwischen den Vektoren (Vektor-DB) und den Metadaten (Document Store), da diese asynchron über die Ingest-Pipeline befüllt werden.

**Trade-Off (Recall):** Um die ≤50 ms für die ANN-Suche zu garantieren, musste der HNSW-Parameter ef auf einen Wert reduziert werden, der einen geringen, aber akzeptablen Verlust an Recall (Wiederfindungsrate) im Vergleich zur maximal möglichen Genauigkeit verursacht.
