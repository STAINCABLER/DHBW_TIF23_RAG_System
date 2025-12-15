# Nebenläufigkeit, Sperrprotokolle und Recovery

## 1. Serialisierbarkeit und Konflikte

Ziel der Nebenläufigkeitskontrolle ist, dass parallele Transaktionen sich verhalten, als würden sie in einer **seriellen Reihenfolge** ausgeführt (Serialisierbarkeit).

Zentrale Begriffe:
- **Konflikt**: Zwei Operationen auf demselben Datenelement, von denen mindestens eine ein Schreibzugriff ist.
- **Konflikt-serialisierbarer Schedule**: lässt sich durch Vertauschen nicht-konfligierender Operationen in einen seriellen Schedule überführen.

## 2. Zwei-Phasen-Sperrprotokoll (2PL)

Das **Two-Phase Locking (2PL)** ist ein pessimistisches Verfahren, das Konflikt-Serialisierbarkeit garantiert.

Phasen:
1. **Wachstumsphase**: Transaktion fordert Sperren an, gibt aber keine frei.
2. **Schrumpfphase**: Transaktion gibt Sperren frei, fordert aber keine neuen mehr an.

Varianten:
- **Striktes 2PL**: Schreibsperren werden bis zum Commit gehalten → verhindert „cascading aborts“.
- **Konservatives 2PL**: alle benötigten Sperren werden vor dem Start angefordert → verhindert Deadlocks, reduziert aber Parallelität.

Trade-offs:
- Garantiert Serialisierbarkeit, jedoch mit potenziellen **Deadlocks**, Sperrkonflikten und begrenzter Parallelität.

## 3. MVCC (Multiversion Concurrency Control)

**MVCC** speichert mehrere Versionen eines Datensatzes, sodass Leser eine konsistente Momentaufnahme sehen, während Schreiber neue Versionen anlegen.

Eigenschaften:
- Leser blockieren Schreiber nicht und umgekehrt (für viele Leseszenarien).
- Häufig implementiert als **Snapshot Isolation**, bei der jede Transaktion den Zustand zum Startzeitpunkt sieht.
- MVCC schließt das Isolationslevel „Read Uncommitted“ aus, da Dirty Reads nicht möglich sind.

Vorteile:
- Hoher Durchsatz bei leselastigen Workloads.
- Gute Grundlage für OLTP+OLAP-Hybridsysteme.

Nachteile:
- Mehraufwand für Verwaltung und Garbage Collection alter Versionen.

## 4. ARIES-Logging und Recovery

**ARIES (Algorithms for Recovery and Isolation Exploiting Semantics)** ist ein verbreiteter Recovery-Algorithmus auf Basis von **Write-Ahead Logging (WAL)**

Grundprinzipien:
- **Write-Ahead Logging**: Logeintrag muss dauerhaft geschrieben sein, bevor eine geänderte Seite auf Disk geht.
- **Repeating History during Redo**: Beim Neustart werden alle Aktionen bis zum Crashzeitpunkt erneut ausgeführt.
- **Logging during Undo**: Auch Rücksetz-Operationen werden protokolliert (Compensation Log Records, CLRs).

Recovery-Phasen:
1. **Analyse**: Rekonstruktion aktiver Transaktionen und „dirty pages“.
2. **Redo**: Wiederholung aller notwendigen Änderungen ab dem kleinsten relevanten Log Sequence Number (LSN).
3. **Undo**: Rücknahme aller noch nicht committeten Transaktionen in umgekehrter Reihenfolge.

Zielgrößen:
- Gewährleistung von **Atomicity** und **Durability** der ACID-Eigenschaften.
- Unterstützung von STEAL/NO-FORCE-Pufferstrategien ohne Konsistenzverlust.

## 5. Isolation Levels und Phänomene

Die SQL-Standards definieren vier klassische Isolationsstufen:
- **Read Uncommitted**
- **Read Committed**
- **Repeatable Read**
- **Serializable**

Typische Leseanomalien:
- **Dirty Read**: Lesen uncommitteter Änderungen.
- **Non-Repeatable Read**: Wiederholtes Lesen derselben Zeile liefert unterschiedliche Werte.
- **Phantom Read**: Menge der gelesenen Zeilen ändert sich zwischen zwei gleichen Anfragen.

Matrix (vereinfacht):
- Read Uncommitted: Dirty, Non-Repeatable, Phantoms möglich.
- Read Committed: Dirty verhindert; Non-Repeatable und Phantoms möglich.
- Repeatable Read: Dirty und Non-Repeatable verhindert; Phantoms abhängig von Implementierung.
- Serializable: Alle drei Phänomene verhindert.

## 6. Praxisempfehlungen

- In **OLTP-Systemen** meist Read Committed oder Repeatable Read + gut konfiguriertes Locking/MVCC wählen.
- Für strenge finanzielle Konsistenz: Serializable, ggf. auf Teilmengen der Workloads.
- Deadlock-Analyse und sauberes Fehlerhandling (Retry von Transaktionen) im Anwendungscode einplanen.
