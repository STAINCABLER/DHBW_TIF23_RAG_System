# MODUL 4 — Query Paths bestimmen die Systemkosten

Jetzt ist es Zeit zu lernen,

- welche Schritte eine Anfrage im System durchläuft,
- welche davon kritisch sind (→ beeinflussen die Antwortzeit),
- welche davon nicht kritisch sind (→ dürfen langsam sein),
- welche Datenbanken in diesen Pfaden liegen,
- welches Latenzbudget diese Pfade haben.

Modul 4 beantwortet also die Frage:

👉 „Welche Daten müssen in welcher Reihenfolge wie schnell gelesen oder geschrieben werden?"

## 1. Ziel des Moduls

Nach diesem Modul kannst du:

- kritische Query Paths in einem System identifizieren,
- erkennen, welche Queries die Latenz dominieren,
- verstehen, warum Datenmodelle zuerst auf Query Paths optimiert werden müssen,
- die richtigen Fragen stellen, bevor du ein Datenmodell baust,
- und für dein Capstone-Projekt klar definieren:
  Welche Daten werden wie abgefragt – und was kostet das?

Dieses Modul ist der Wendepunkt im Kurs:
→ Deine Architektur wird jetzt realistisch.

## 2. Warum Query Paths wichtiger sind als das Datenmodell

Ein Query Path ist der konkrete Ablauf von Datenbankzugriffen, den dein System für eine einzige Anfrage durchführt.

Beispiele (Customer-Service-RAG):

### Path A — RAG-Antwort für eine Kundenfrage

- Rate-Limit prüfen → Redis
- Kundendaten laden → Postgres
- Query Embedding berechnen → (LLM)
- ANN-Suche → pgvector
- 5–10 Chunks laden → Mongo
- Antwort generieren

### Path B — Kundendaten aktualisieren

- Authentication
- Berechtigungen prüfen
- Profil lesen
- Profil updaten
- Änderung loggen

Jeder dieser Schritte hat eine Latenz – und die Summe bestimmt die User Experience.

**Merksatz:**

Ein System ist immer nur so schnell wie sein langsamster Query Path.

## 3. Das Kernprinzip: Modellierung folgt Query Paths, nicht Tabellenideen

**Falscher Startpunkt (klassisch):**
„Wie speichere ich die Daten am schönsten?"

**Richtiger Startpunkt (professionell):**
„Welche Queries müssen garantiert schnell sein – und wie strukturiere ich die Daten dafür?"

Beispiele:

- Chunks werden im kritischen Pfad gelesen → Modell muss Read-optimal sein.
- Kundendaten brauchen ACID → Modell muss konsistent aktualisierbar sein.
- Embeddings werden über ANN gesucht → Indexierung bestimmt alles.
- Chat-Historien haben Append-only und seltenes Lesen → Modell muss billig schreiben.

Das Datenmodell folgt also immer:

Query Path → Zugriffsszenario → Datenmodell

## 4. Die vier Arten von Query Paths (professionelle Klassifikation)

Jeder Query Path ist einer dieser vier Typen:

### 4.1 Critical (Blocking)

Wenn dieser Pfad langsam ist, spürt der Nutzer es direkt.

Beispiele:

- ANN-Suche
- Chunk-Lesen
- Kundenprofil-Lookup

### 4.2 Warm Path (häufig, aber nicht zeitkritisch)

Häufig ausgeführt, aber nicht absolut kritisch fürs UI.

Beispiele:

- Monitoring-Writes
- Embedding-Persistenz

### 4.3 Cold Path (selten, aber teuer)

Selten ausgeführt, aber potenziell extrem rechenintensiv.

Beispiele:

- Re-Embedding ganzer Doku-Sammlung
- Neu-Ingestion von 1000 PDFs

### 4.4 Background / Async

Darf immer langsam sein.

Beispiele:

- Logs in Timescale
- Cache-Warmup
- Analysen

Warum das wichtig ist:
→ Nur Critical Paths bestimmen réellement, wie du modellierst.

## 5. Wie du Query Paths im Capstone identifizierst (Checkliste)

Für jedes Datenobjekt stellst du:

- Wie oft wird es gelesen?
- Wie oft wird es geschrieben?
- Ist die Operation im kritischen Pfad?
- Kann sie asynchron sein?
- Welche Latenz ist akzeptabel (Zahl!)?
- Welche Datenbank ist involviert?
- Wie viele Roundtrips verursacht es?

Dein Capstone wird nur dann gut, wenn du diese Liste explizit abarbeitest.

## 6. Query Path Mapping – am kompletten Beispiel

Hier ein vollständiges Beispiel eines RAG-Query Paths:

| Schritt | Operation | DB | Typ | Erwartete Latenz |
|---------|-----------|-----|----------|------------------|
| 1 | Rate-Limit lesen | Redis | Critical | 1–2 ms |
| 2 | Kundendaten laden | Postgres | Critical | 5–20 ms |
| 3 | Embedding berechnen | LLM | Critical | 20–60 ms |
| 4 | ANN-Suche | pgvector | Critical | 5–15 ms |
| 5 | 5–10 Chunks lesen | Mongo | Critical | 10–50 ms |
| 6 | Antwort generieren | LLM | Critical | 50–120 ms |

Was du daraus lernst:

- Kundendaten dürfen nicht in Mongo liegen → Falsche Konsistenz.
- Chunks dürfen nicht in PostgreSQL liegen → JSONB zu langsam.
- Embeddings gehören nicht in Mongo → falsches Suchmodell.

Das ist echte Architektur.

## 7. Bezug zum Capstone-Projekt (klar & prüfrelevant)

In der schriftlichen Abgabe musst du zeigen:

- Welche Query Paths dein System hat
- Welche davon kritisch sind
- Welche Datenbanken involviert sind
- Welche Latenzanforderungen gelten
- Warum dein Datenmodell genau für diese Paths optimiert ist

Bewertet wird vor allem:

- ob du kritische Pfade korrekt erkannt hast
- ob dein Modell die kritischen Pfade optimiert
- ob du unnötige Roundtrips vermeidest
- ob deine Wahl der DB die Pfade stützt statt blockiert

Wenn du das nicht machst, ist das Datenmodell unbewertbar.

## 8. Mini-Aufgabe (10–15 Minuten)

### Gruppenarbeit

Gegeben:

„Ein RAG-System lädt für jeden Request:

- ein Kundenprofil
- ein Query-Embedding
- 6 Chunks
- loggt 1 Event
- aktualisiert das Rate-Limit"

Aufgabe:

1. Zeichne den Query Path (Stichworte reichen).
2. Markiere, was kritisch ist.
3. Schlage je Schritt eine mögliche Datenbank vor.
4. Begründe kurz, warum.

## 9. Quick-Check – Prüfe dein Verständnis

Kannst du:

- sagen, welche Pfade kritisch sind und warum?
- erklären, warum Datenmodelle auf Query Paths beruhen?
- Query Paths deines Capstones beschreiben?
- begründen, welche Datenbank im Critical Path steht?

Wenn ja → du bist bereit für Modul 5.

## 10. LLM-Assist (optional)

Nutze diese Prompts, um deine Query Paths zu validieren:

- „Welche Schritte liegen im kritischen Pfad meiner Capstone-Architektur?"
- „Welche Abfragen verursachen die höchste Latenz?"
- „Welche Roundtrips könnte ich vermeiden?"
- „Welche DB-Wahl wäre riskant für meinen kritischen Pfad?"
