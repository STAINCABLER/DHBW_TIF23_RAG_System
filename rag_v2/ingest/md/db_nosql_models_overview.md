# NoSQL-Datenmodelle im Überblick

## 1. Motivation für NoSQL

NoSQL-Datenbanken entstanden, um Anforderungen zu adressieren, bei denen klassische relationale Systeme an Grenzen stoßen:
- Massive horizontale Skalierung.
- Flexible oder sich schnell ändernde Schemata.
- Verteilte Systeme mit eventual consistency.

Statt eines einheitlichen Modells existieren verschiedene Spezialmodelle.

## 2. Schlüssel-Wert-Speicher (Key-Value Stores)

Datenmodell:
- Abbildung von **Schlüssel → Wert**.
- Wert ist meist opaque für die Datenbank (Blob, JSON, Binärdaten).

Stärken:
- Extrem schnell für **exakte Key-Lookups**.
- Sehr einfache Replikation und Sharding.

Typische Use-Cases:
- Caching (z. B. Sessions, Feature Flags).
- Konfigurations- und Profil-Daten.

Beispiele: Redis, Amazon DynamoDB (Key-Value-Modus).

## 3. Dokumentenorientierte Datenbanken

Datenmodell:
- Speicherung von **Dokumenten** (oft JSON/BSON) mit variabler Struktur.
- Sammlungen (Collections) statt Tabellen.

Stärken:
- Flexibles Schema (Schema-on-Read).
- Gute Unterstützung für verschachtelte Strukturen und Aggregationspipelines.

Typische Use-Cases:
- Content-Management, Benutzerprofile, Produktkataloge.

Beispiele: MongoDB, CouchDB.

## 4. Spaltenfamilien-/Wide-Column-Stores

Datenmodell:
- Mehrdimensionale Key-Value-Struktur mit **Zeilenkey** und dynamischen Spaltenfamilien.
- Zeilen können sehr viele, auch spärlich besetzte Spalten haben.
- 
Stärken:
- Hohe Schreib- und Leseskalierung über viele Knoten.
- Geeignet für Zeitreihen, Logdaten und Metriken.

Typische Use-Cases:
- IoT/Telemetry, Event-Streams, große Zeitreihen.

Beispiele: Apache Cassandra, HBase.

## 5. Graphdatenbanken

Datenmodell:
- **Knoten (Nodes)** mit Eigenschaften.
- **Kanten (Edges)** mit Richtung und Eigenschaften zur Modellierung von Beziehungen.

Stärken:
- Sehr effizient für Traversalen und Pfadabfragen.
- Modelliert komplexe Beziehungsnetze natürlich.

Typische Use-Cases:
- Soziale Netzwerke, Empfehlungsmaschinen, Betrugserkennung.

Beispiele: Neo4j, ArangoDB, JanusGraph.

## 6. Vergleich zu relationalen Systemen

- Relationale Systeme optimieren **Konsistenz und Ad-hoc-Abfragen** auf stark strukturierten Daten.
- NoSQL-Systeme optimieren oft **Skalierbarkeit, Verfügbarkeit und flexible Schemata**, häufig auf Kosten starker Konsistenz.

In modernen Architekturen sind Mischlandschaften („Polyglot Persistence“) üblich: Jede Domäne nutzt das Datenmodell, das fachlich und technisch am besten passt.
