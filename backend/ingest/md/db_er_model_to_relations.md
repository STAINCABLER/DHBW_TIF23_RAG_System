# ER-Modell und relationale Schemaableitung

## 1. Rolle des ER-Modells im Designprozess

Das **Entity-Relationship-Modell (ER-Modell)** wird im logischen Design genutzt, um Anforderungen in ein konzeptionelles Schema zu überführen, bevor Relationen definiert werden.[52][55][58]

Typischer Ablauf:[52][55][59]
- Anforderungen erheben (Entitäten, Beziehungen, Kardinalitäten, Attribute).
- ER-Diagramm erstellen (Chen, Barker/Oracle oder UML-ähnliche Notation).[52][58]
- ER-Schema in relationale Schemata überführen.
- Schema mit Normalisierungstheorie validieren (Normalformen, funktionale Abhängigkeiten).[12][18][52]

## 2. Zentrale Bausteine des ER-Modells

- **Entitätstyp**: Menge gleichartiger Objekte (z. B. Kunde, Bestellung).[52][55]
- **Beziehungstyp**: Verknüpft Entitäten (z. B. Kunde–platziert→Bestellung).
- **Attribute**: Eigenschaften von Entitäten/Beziehungen; können einfach, zusammengesetzt oder mehrwertig sein.[52][58]
- **Schlüsselattribute**: identifizieren Entitäten eindeutig.

Beziehungs-Kardinalitäten:
- 1:1, 1:n, n:m; zusätzlich Teilnahme-Constraints (obligatorisch/optional).[52][55]

## 3. Von ER zu Relationen – Standardabbildungsregeln

Typische Regeln nach Lehrbuch (Silberschatz/Korth/Sudarshan):[52][58]

1. **Starke Entitätstypen**
   - Für jeden starken Entitätstyp eine Relation mit allen einfachen Attributen.
   - Schlüsselattribut(e) werden Primärschlüssel.

2. **Schwache Entitätstypen**
   - Relation mit eigenen Attributen plus Primärschlüssel des identifizierenden Entitätstyps.
   - Primärschlüssel = (Partial Key, identifizierender Schlüssel).[52]

3. **1:n-Beziehungen**
   - Fremdschlüssel auf der „n“-Seite, der auf den Primärschlüssel der „1“-Seite zeigt.[52][55]

4. **n:m-Beziehungen**
   - Eigene Relation mit:
     - Fremdschlüssel auf beide beteiligten Entitätstypen.
     - Evtl. eigenen Attributen der Beziehung.
     - Kombinierter Primärschlüssel aus den beiden Fremdschlüsseln (oder zusätzlichem Surrogat).[52]

5. **Ternäre und höhere Beziehungen**
   - Relation mit Fremdschlüsseln auf alle beteiligten Entitätstypen + eigenen Attributen.

## 4. Spezialisierung/Generalisierung

- **Generalisierung**: gemeinsame Oberklasse (z. B. Person) für mehrere Unterklassen (Kunde, Mitarbeiter).[52][58]
- Wichtige Designentscheidungen:
  - Überlappende vs. disjunkte Unterklassen.
  - Totale vs. partielle Spezialisierung.

Umsetzung im relationalen Schema:[52][58]
- **Class-Table Inheritance**: eigene Tabelle pro Klasse/Unterklasse.
- **Single-Table Inheritance**: eine große Tabelle mit Diskriminatorattribut.
- **Concrete-Table Inheritance**: nur Tabellen für konkrete Unterklassen mit redundanten Spalten.

## 5. Qualitätskriterien guter ER-Modelle

- Klare, präzise Namensgebung der Entitäten und Attribute.[53][56]
- Eindeutige Kardinalitäten und Teilnahme-Constraints.
- Keine übermäßig großen Entitätstypen „vom Typ Gottobjekt“.
- Frühzeitige Identifikation natürlicher Schlüssel und funktionaler Abhängigkeiten.[12][13][18]

Gut ausgearbeitete ER-Modelle erleichtern Normalisierung, Schema-Evolution und spätere Performanceoptimierung deutlich.[52][56][58]
