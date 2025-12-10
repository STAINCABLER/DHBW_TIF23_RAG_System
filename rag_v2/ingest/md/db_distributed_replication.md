# Verteilte Datenbanken, Replikation, Sharding und Konsistenzmodelle

## 1. Verteilte Datenbanken – Motivation

Verteilte Datenbanken verteilen Daten über mehrere Knoten, um **Skalierbarkeit**, **Verfügbarkeit** und **Fehlertoleranz** zu erhöhen.

Kernmechanismen:
- **Replikation**: mehrfache Speicherung derselben Daten auf verschiedenen Knoten.
- **Partitionierung/Sharding**: Aufteilung der Datenmenge auf logische/physische Teilmengen.

## 2. Replikation

Ziele:
- Erhöhung der Leseskalierung (Reads über Replikate verteilen).
- Bessere Verfügbarkeit bei Knotenausfälle

Modelle:
- **Primär-Sekundär (Leader-Follower)**: Schreibzugriffe nur auf den Leader; Replikation synchron oder asynchron auf Follower.[42]
- **Multi-Leader**: Mehrere Knoten akzeptieren Writes, Konfliktauflösung notwendig.

Trade-offs:
- **Synchrone Replikation**: starke Konsistenz, aber höhere Latenz.
- **Asynchrone Replikation**: bessere Latenz/Verfügbarkeit, aber temporär schwächere Konsistenz.

## 3. Sharding / Partitionierung

**Sharding** teilt eine große logische Tabelle in mehrere physische Teilmengen (Shards), die über Knoten verteilt werden.

Typische Strategien:
- **Hash-basiert**: Verteilung über Hash des Shard-Keys → gute Lastverteilung, aber Range-Queries über mehrere Shards nötig.
- **Range-basiert**: Partitionierung nach Wertebereichen (z. B. Datum, ID-Bereich) → effiziente Range-Queries, Risiko „hot shards“.

Besondere Aspekte bei Vektor-/NoSQL-Systemen:
- Sharding nach **Ähnlichkeit/Clustern** (z. B. k-means) zur Reduktion der abgefragten Shards bei Ähnlichkeitssuchen.

## 4. CAP-Theorem

Das **CAP-Theorem** beschreibt einen fundamentalen Zielkonflikt in verteilten Datenspeichern:
- **Consistency (C)**: Jede Leseoperation sieht den aktuellsten Commit oder einen Fehler.
- **Availability (A)**: Jede Anfrage erhält eine (nicht notwendigerweise aktuelle) Antwort.
- **Partition tolerance (P)**: Das System funktioniert trotz Netzpartitionen weiter.

Aussage:
- Unter Netzausfall (Partition) kann ein System nicht gleichzeitig strikte Konsistenz und volle Verfügbarkeit garantieren; es muss zwischen **CP** und **AP** wählen.

Beispiele (vereinfacht):
- **CP-Systeme**: priorisieren Konsistenz; im Zweifel werden Requests abgelehnt/blockiert.
- **AP-Systeme**: priorisieren Verfügbarkeit; nehmen Inkonsistenzen temporär in Kauf und gleichen später ab.

## 5. Konsistenzmodelle jenseits von ACID

In verteilten Systemen kommen oft abgeschwächte Konsistenzmodelle zum Einsatz:
- **Starke (lineare) Konsistenz**: jede Operation sieht eine globale, total geordnete Folge von Updates.
- **Eventual Consistency**: bei ausbleibenden Updates konvergieren alle Replikate langfristig auf denselben Zustand.
- **Causal Consistency**: Operationen, die kausal zusammenhängen, werden von allen Knoten in derselben Reihenfolge gesehen.

Diese Modelle bilden die Basis vieler NoSQL- und Cloud-Datenbanken.

## 6. Praxisleitlinien

- Kritische, strikt konsistente Kernkonten (z. B. Finanztransaktionen) als **CP** auslegen, ggf. mit synchroner Replikation.
- Leseintensive, tolerante Teile (z. B. Caches, Zähler, Logdaten) eher **AP**/eventual consistent.
- Shard-Key sorgfältig wählen (z. B. nicht rein monoton, um Hotspots zu vermeiden).
- Monitoring und Rebalancing-Mechanismen einplanen, um ungleich verteilte Shards zu korrigieren.
