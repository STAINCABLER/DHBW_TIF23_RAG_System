# Schema-Design-Best-Practices für relationale Datenbanken

## 1. Primärschlüssel und Identität

- Jede Tabelle sollte einen **stabilen Primärschlüssel** haben.
- Bei unsicheren natürlichen Schlüsseln (z. B. E-Mail, Name) besser **Surrogatschlüssel** (INTEGER/BIGINT, UUID) verwenden.
- Primärschlüssel möglichst kurz halten (wichtig für Indexgröße und Fremdschlüssel).

## 2. Normalisierung mit Augenmaß

- Bis mindestens **3NF**, in vielen OLTP-Fällen **BCNF**, normalisieren, um Redundanz und Anomalien zu vermeiden.
- Denormalisierung nur gezielt und mit Klartext-Begründung einsetzen (meist für Reporting/Analytics).

## 3. Klare Namenskonventionen

- Konsistente, sprechende Namen (snake_case oder lowerCamelCase).
- Tabellen im Singular oder Plural, aber einheitlich.
- Fremdschlüsselspalten eindeutig erkennbar (z. B. customer_id, order_id).

## 4. Datentypen und Constraints

- Datentypen so restriktiv wie sinnvoll wählen (z. B. INTEGER statt VARCHAR für IDs).
- **NOT NULL**, **CHECK**, **UNIQUE**, **FOREIGN KEY** aktiv nutzen, um Geschäftsregeln im Schema zu verankern.
- Zeitstempel konsistent (z. B. TIMESTAMP WITH TIME ZONE) und in UTC speichern.

## 5. Indexierungsstrategie

- Indexe primär auf:
  - Primärschlüssel und häufige Fremdschlüssel.
  - Spalten in WHERE-/JOIN-Bedingungen und ORDER BY/GROUP BY-Klauseln.
- Zu viele Indexe vermeiden, da sie Schreiboperationen verteuern.
- Regelmäßig Statistiken aktualisieren und ungenutzte Indexe entfernen.

## 6. Beziehungen und Kardinalitäten

- 1:n-Beziehungen klar per Fremdschlüssel modellieren; n:m-Beziehungen über Join-Tabellen.
- „Optionale“ Beziehungen nur dann zulassen, wenn das fachlich wirklich sinnvoll ist (NULL-FKs bewusst einsetzen).

## 7. Historisierung und Auditing

- Für fachlich relevante Änderungen Historisierungstabellen oder Gültigkeitszeiträume (valid_from/valid_to) vorsehen.
- Technische Nachvollziehbarkeit via Audit-Tabellen oder Änderungs-Trigger.

## 8. Schema-Evolution und Versionierung

- Änderungen an produktiven Schemata ausschließlich über **Migrationen** (z. B. Liquibase, Flyway) durchführen.
- Abwärtskompatibel migrieren (zuerst Add, dann Deploy, dann Remove von Altstrukturen).

## 9. Sicherheit und Datenschutz

- Zugriff über **Least Privilege**: getrennte Rollen für Applikation, Admin, Reporting.
- Sensible Daten (z. B. personenbezogene Informationen) verschlüsseln oder pseudonymisieren, wo notwendig.

## 10. Dokumentation und Modelle

- ER-Diagramme und Schemadokumentation aktuell halten (z. B. per generiertem Schema-Diagramm).
- Wichtige Designentscheidungen (z. B. bewusst nicht normalisierte Tabellen) schriftlich begründen.
