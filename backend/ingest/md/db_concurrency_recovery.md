# Nebenläufigkeit, Sperrprotokolle und Recovery

## 1. Serialisierbarkeit und Konflikte

Ziel der Nebenläufigkeitskontrolle ist, dass parallele Transaktionen sich verhalten, als würden sie in einer **seriellen Reihenfolge** ausgeführt (Serialisierbarkeit).[2][5][8]

Zentrale Begriffe:
- **Konflikt**: Zwei Operationen auf demselben Datenelement, von denen mindestens eine ein Schreibzugriff ist.[2][5][8]
- **Konflikt-serialisierbarer Schedule**: lässt sich durch Vertauschen nicht-konfligierender Operationen in einen seriellen Schedule überführen.

## 2. Zwei-Phasen-Sperrprotokoll (2PL)

Das **Two-Phase Locking (2PL)** ist ein pessimistisches Verfahren, das Konflikt-Serialisierbarkeit garantiert.[26][29]

Phasen:
1. **Wachstumsphase**: Transaktion fordert Sperren an, gibt aber keine frei.
2. **Schrumpfphase**: Transaktion gibt Sperren frei, fordert aber keine neuen mehr an.

Varianten:
- **Striktes 2PL**: Schreibsperren werden bis zum Commit gehalten → verhindert „cascading aborts“.[26][29]
- **Konservatives 2PL**: alle benötigten Sperren werden vor dem Start angefordert → verhindert Deadlocks, reduziert aber Parallelität.[23][26]

Trade-offs:
- Garantiert Serialisierbarkeit, jedoch mit potenziellen **Deadlocks**, Sperrkonflikten und begrenzter Parallelität.[26][29]

## 3. MVCC (Multiversion Concurrency Control)

**MVCC** speichert mehrere Versionen eines Datensatzes, sodass Leser eine konsistente Momentaufnahme sehen, während Schreiber neue Versionen anlegen.[1][7][10]

Eigenschaften:[1][7][10]
- Leser blockieren Schreiber nicht und umgekehrt (für viele Leseszenarien).
- Häufig implementiert als **Snapshot Isolation**, bei der jede Transaktion den Zustand zum Startzeitpunkt sieht.
- MVCC schließt das Isolationslevel „Read Uncommitted“ aus, da Dirty Reads nicht möglich sind.[1][7]

Vorteile:
- Hoher Durchsatz bei leselastigen Workloads.
- Gute Grundlage für OLTP+OLAP-Hybridsysteme.[4]

Nachteile:
- Mehraufwand für Verwaltung und Garbage Collection alter Versionen.[1][7]

## 4. ARIES-Logging und Recovery

**ARIES (Algorithms for Recovery and Isolation Exploiting Semantics)** ist ein verbreiteter Recovery-Algorithmus auf Basis von **Write-Ahead Logging (WAL)**.[41][44][47][50]

Grundprinzipien:[44][50]
- **Write-Ahead Logging**: Logeintrag muss dauerhaft geschrieben sein, bevor eine geänderte Seite auf Disk geht.
- **Repeating History during Redo**: Beim Neustart werden alle Aktionen bis zum Crashzeitpunkt erneut ausgeführt.
- **Logging during Undo**: Auch Rücksetz-Operationen werden protokolliert (Compensation Log Records, CLRs).

Recovery-Phasen:[41][47][50]
1. **Analyse**: Rekonstruktion aktiver Transaktionen und „dirty pages“.
2. **Redo**: Wiederholung aller notwendigen Änderungen ab dem kleinsten relevanten Log Sequence Number (LSN).
3. **Undo**: Rücknahme aller noch nicht committeten Transaktionen in umgekehrter Reihenfolge.

Zielgrößen:
- Gewährleistung von **Atomicity** und **Durability** der ACID-Eigenschaften.[27][41][47]
- Unterstützung von STEAL/NO-FORCE-Pufferstrategien ohne Konsistenzverlust.[44][50]

## 5. Isolation Levels und Phänomene

Die SQL-Standards definieren vier klassische Isolationsstufen:[28]
- **Read Uncommitted**
- **Read Committed**
- **Repeatable Read**
- **Serializable**

Typische Leseanomalien:[28][22][25]
- **Dirty Read**: Lesen uncommitteter Änderungen.
- **Non-Repeatable Read**: Wiederholtes Lesen derselben Zeile liefert unterschiedliche Werte.
- **Phantom Read**: Menge der gelesenen Zeilen ändert sich zwischen zwei gleichen Anfragen.

Matrix (vereinfacht):[25][28]
- Read Uncommitted: Dirty, Non-Repeatable, Phantoms möglich.
- Read Committed: Dirty verhindert; Non-Repeatable und Phantoms möglich.
- Repeatable Read: Dirty und Non-Repeatable verhindert; Phantoms abhängig von Implementierung.
- Serializable: Alle drei Phänomene verhindert.

## 6. Praxisempfehlungen

- In **OLTP-Systemen** meist Read Committed oder Repeatable Read + gut konfiguriertes Locking/MVCC wählen.[22][30]
- Für strenge finanzielle Konsistenz: Serializable, ggf. auf Teilmengen der Workloads.[21][24][27]
- Deadlock-Analyse und sauberes Fehlerhandling (Retry von Transaktionen) im Anwendungscode einplanen.
