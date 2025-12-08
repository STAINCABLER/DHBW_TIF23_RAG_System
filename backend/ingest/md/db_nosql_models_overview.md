# NoSQL-Datenmodelle im Überblick

## 1. Motivation für NoSQL

NoSQL-Datenbanken entstanden, um Anforderungen zu adressieren, bei denen klassische relationale Systeme an Grenzen stoßen:
- Massive horizontale Skalierung.
- Flexible oder sich schnell ändernde Schemata.
- Verteilte Systeme mit eventual consistency.[51][54][57][60]

Statt eines einheitlichen Modells existieren verschiedene Spezialmodelle.

## 2. Schlüssel-Wert-Speicher (Key-Value Stores)

Datenmodell:[51][54][57][60]
- Abbildung von **Schlüssel → Wert**.
- Wert ist meist opaque für die Datenbank (Blob, JSON, Binärdaten).

Stärken:
- Extrem schnell für **exakte Key-Lookups**.
- Sehr einfache Replikation und Sharding.

Typische Use-Cases:
- Caching (z. B. Sessions, Feature Flags).
- Konfigurations- und Profil-Daten.

Beispiele: Redis, Amazon DynamoDB (Key-Value-Modus).[51][57][60]

## 3. Dokumentenorientierte Datenbanken

Datenmodell:[51][57][60]
- Speicherung von **Dokumenten** (oft JSON/BSON) mit variabler Struktur.
- Sammlungen (Collections) statt Tabellen.

Stärken:
- Flexibles Schema (Schema-on-Read).
- Gute Unterstützung für verschachtelte Strukturen und Aggregationspipelines.

Typische Use-Cases:
- Content-Management, Benutzerprofile, Produktkataloge.[51][57]

Beispiele: MongoDB, CouchDB.[51][54][60]

## 4. Spaltenfamilien-/Wide-Column-Stores

Datenmodell:[51][54][57][60]
- Mehrdimensionale Key-Value-Struktur mit **Zeilenkey** und dynamischen Spaltenfamilien.
- Zeilen können sehr viele, auch spärlich besetzte Spalten haben.[54][57]

Stärken:
- Hohe Schreib- und Leseskalierung über viele Knoten.
- Geeignet für Zeitreihen, Logdaten und Metriken.

Typische Use-Cases:
- IoT/Telemetry, Event-Streams, große Zeitreihen.[51][54][57]

Beispiele: Apache Cassandra, HBase.[51][54][57][60]

## 5. Graphdatenbanken

Datenmodell:[51][57][60]
- **Knoten (Nodes)** mit Eigenschaften.
- **Kanten (Edges)** mit Richtung und Eigenschaften zur Modellierung von Beziehungen.

Stärken:
- Sehr effizient für Traversalen und Pfadabfragen.
- Modelliert komplexe Beziehungsnetze natürlich.[51][57]

Typische Use-Cases:
- Soziale Netzwerke, Empfehlungsmaschinen, Betrugserkennung.[51][57][60]

Beispiele: Neo4j, ArangoDB, JanusGraph.[51][57]

## 6. Vergleich zu relationalen Systemen

- Relationale Systeme optimieren **Konsistenz und Ad-hoc-Abfragen** auf stark strukturierten Daten.[11][14][17][20]
- NoSQL-Systeme optimieren oft **Skalierbarkeit, Verfügbarkeit und flexible Schemata**, häufig auf Kosten starker Konsistenz.[43][46][49][60]

In modernen Architekturen sind Mischlandschaften („Polyglot Persistence“) üblich: Jede Domäne nutzt das Datenmodell, das fachlich und technisch am besten passt.[51][53][56][60]
