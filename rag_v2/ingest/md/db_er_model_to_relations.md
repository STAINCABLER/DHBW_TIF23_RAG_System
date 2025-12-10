# ER-Modell und relationale Schemaableitung

## 1. Rolle des ER-Modells im Designprozess

Das **Entity-Relationship-Modell (ER-Modell)** wird im logischen Design genutzt, um Anforderungen in ein konzeptionelles Schema zu überführen, bevor Relationen definiert werden.

Typischer Ablauf:
- Anforderungen erheben (Entitäten, Beziehungen, Kardinalitäten, Attribute).
- ER-Diagramm erstellen (Chen, Barker/Oracle oder UML-ähnliche Notation).
- ER-Schema in relationale Schemata überführen.
- Schema mit Normalisierungstheorie validieren (Normalformen, funktionale Abhängigkeiten).

## 2. Zentrale Bausteine des ER-Modells

- **Entitätstyp**: Menge gleichartiger Objekte (z. B. Kunde, Bestellung).
- **Beziehungstyp**: Verknüpft Entitäten (z. B. Kunde–platziert→Bestellung).
- **Attribute**: Eigenschaften von Entitäten/Beziehungen; können einfach, zusammengesetzt oder mehrwertig sein.
- **Schlüsselattribute**: identifizieren Entitäten eindeutig.

Beziehungs-Kardinalitäten:
- 1:1, 1:n, n:m; zusätzlich Teilnahme-Constraints (obligatorisch/optional).

## 3. Von ER zu Relationen – Standardabbildungsregeln

Typische Regeln nach Lehrbuch (Silberschatz/Korth/Sudarshan):

1. **Starke Entitätstypen**
   - Für jeden starken Entitätstyp eine Relation mit allen einfachen Attributen.
   - Schlüsselattribut(e) werden Primärschlüssel.

2. **Schwache Entitätstypen**
   - Relation mit eigenen Attributen plus Primärschlüssel des identifizierenden Entitätstyps.
   - Primärschlüssel = (Partial Key, identifizierender Schlüssel).

3. **1:n-Beziehungen**
   - Fremdschlüssel auf der „n“-Seite, der auf den Primärschlüssel der „1“-Seite zeigt.

4. **n:m-Beziehungen**
   - Eigene Relation mit:
     - Fremdschlüssel auf beide beteiligten Entitätstypen.
     - Evtl. eigenen Attributen der Beziehung.
     - Kombinierter Primärschlüssel aus den beiden Fremdschlüsseln (oder zusätzlichem Surrogat).

5. **Ternäre und höhere Beziehungen**
   - Relation mit Fremdschlüsseln auf alle beteiligten Entitätstypen + eigenen Attributen.

## 4. Spezialisierung/Generalisierung

- **Generalisierung**: gemeinsame Oberklasse (z. B. Person) für mehrere Unterklassen (Kunde, Mitarbeiter).
- Wichtige Designentscheidungen:
  - Überlappende vs. disjunkte Unterklassen.
  - Totale vs. partielle Spezialisierung.

Umsetzung im relationalen Schema:
- **Class-Table Inheritance**: eigene Tabelle pro Klasse/Unterklasse.
- **Single-Table Inheritance**: eine große Tabelle mit Diskriminatorattribut.
- **Concrete-Table Inheritance**: nur Tabellen für konkrete Unterklassen mit redundanten Spalten.

## 5. Qualitätskriterien guter ER-Modelle

- Klare, präzise Namensgebung der Entitäten und Attribute.
- Eindeutige Kardinalitäten und Teilnahme-Constraints.
- Keine übermäßig großen Entitätstypen „vom Typ Gottobjekt“.
- Frühzeitige Identifikation natürlicher Schlüssel und funktionaler Abhängigkeiten.

Gut ausgearbeitete ER-Modelle erleichtern Normalisierung, Schema-Evolution und spätere Performanceoptimierung deutlich.
