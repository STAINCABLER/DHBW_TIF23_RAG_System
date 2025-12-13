# Indexierung und Anfrageverarbeitung

## 1. Grundlagen der Indexierung

Ein **Index** ist eine zusätzliche Datenstruktur, die den Zugriff auf Zeilen einer Tabelle beschleunigt, indem sie Suchattribute sortiert speichert und so die Anzahl der zu prüfenden Seiten reduziert. RDBMS setzen standardmäßig häufig **B-Baum-Varianten (B+ Bäume)** ein.

Zentrale Ziele:
- Reduktion von I/O-Zugriffen
- Unterstützung von Bereichsanfragen und Sortierungen
- Sicherstellung von Eindeutigkeit (z. B. für Primärschlüssel)

Typische Indexarten:
- **Clustered Index**: definiert die physische Sortierordnung der Tabelle.
- **Non-Clustered Index**: separate Struktur mit Zeigern (RID/PK) auf Datenzeilen.
- **Unique Index**: erzwingt Eindeutigkeit der indizierten Spalten.

## 2. B-Baum-Indizes

**B-Bäume** sind balancierte Suchbäume mit folgendem Eigenschaften:
- Alle Blätter liegen auf derselben Höhe.
- Jeder Knoten enthält eine sortierte Menge von Schlüsseln und Kindzeigern.
- Suchen, Einfügen und Löschen laufen in \(O(\log n)\).

Vorteile:
- Sehr gut für **Bereichsanfragen** (\(>\), \(<\), BETWEEN) und für ORDER BY geeignet.
- Weit verbreitet in OLTP-Datenbanken (PostgreSQL, MySQL/InnoDB, Oracle, SQL Server).

Einsatzempfehlungen:
- Primärschlüssel und häufig genutzte Fremdschlüssel.
- Spalten, die in WHERE, JOIN oder ORDER BY/GROUP BY vorkommen.

## 3. Hash-Indizes

**Hash-Indizes** verwenden eine Hash-Funktion, um einen Suchschlüssel direkt auf einen Bucket abzubilden.

Eigenschaften:
- Sehr schnell für **exakte Gleichheitsabfragen** (=).
- Nicht geeignet für Bereichsanfragen oder ORDER BY.

Typische Einsatzszenarien:
- Lookups auf hochselektiven Schlüsseln mit Gleichheitsvergleichen.
- Caching-ähnliche Zugriffe mit bekannten Schlüsseln.

## 4. Kostenbasierte Anfrageoptimierung

Moderne DBMS setzen einen **kostenbasierten Optimierer (CBO)** ein, der aus vielen äquivalenten physikalischen Ausführungsplänen den kostengünstigsten wählt.

Wesentliche Schritte:
1. **Logischen Plan erzeugen** (basierend auf SQL und relationaler Algebra).
2. **Alternativen generieren** (Join-Reihenfolgen, Join-Algorithmen, Index-Nutzung).
3. **Kosten schätzen** anhand von Statistiken:
   - Kardinalität (Zeilenanzahl)
   - Selektivität von Prädikaten
   - Verteilung von Werten
4. **Plan mit minimalen Kosten auswählen**.

## 5. Wichtige Join-Algorithmen

- **Nested Loop Join**:
  - Einfache Implementierung.
  - Gut, wenn die innere Seite stark eingeschränkt und/oder indiziert ist.
- **Hash Join**:
  - Baut Hash-Tabelle auf der kleineren Eingabe, probt dann mit der größeren.
  - Sehr effizient für Gleich-Joins ohne Sortierung.
- **Sort-Merge Join**:
  - Beide Eingaben werden sortiert, dann linear gemergt.
  - Vorteile bei bereits sortierten Eingaben (z. B. durch Indizes).

## 6. Praktische Tuning-Regeln

- **Selektive Prädikate zuerst auswerten** (Filter Pushdown).
- Nur dort indizieren, wo **Leselast und Selektivität** den Schreib-Overhead rechtfertigen.
- Statistiken regelmäßig aktualisieren, da sie Grundlage der Kostenabschätzung sind.
