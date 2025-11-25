# Datenbankarchitektur des RAG-Systems

## Übersicht

Das Datenbankenberatungs-RAG-System nutzt eine **Hybrid-Datenbankarchitektur** mit drei spezialisierten Datenbanksystemen:

- **MongoDB**: Dokumentenspeicherung für Beratungsinhalte
- **PostgreSQL**: Relationale Metadaten und Strukturdaten
- **Redis**: Caching und Echtzeit-Datenverarbeitung

## Architekturdiagramm

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
    ┌────▼────────────────────┐
    │   RAG Query Engine       │
    │   (Python Backend)       │
    └────┬────────────────────┘
         │
    ┌────┴──────────┬──────────┬──────────┐
    │               │          │          │
    ▼               ▼          ▼          ▼
┌──────────┐  ┌──────────┐ ┌─────────┐ ┌──────────┐
│  Redis   │  │ MongoDB  │ │PostgreSQL│ │Vector DB │
│  Cache   │  │Documents │ │Metadata  │ │Embeddings│
└──────────┘  └──────────┘ └─────────┘ └──────────┘
    │               │          │          │
    └────┬──────────┴──────────┴──────────┘
         │
    ┌────▼─────────────┐
    │  Recommendation  │
    │     Engine       │
    └──────────────────┘
         │
    ┌────▼────────────┐
    │  Best-Match DB  │
    │   Solution      │
    └─────────────────┘
```

## Isolation und Verantwortlichkeiten

### 1. MongoDB - Dokumentenspeicherung
**Verantwortung**: Speicherung von Beratungsinhalten und Datenbankanforderungen

- Beratungsartikel und Dokumentationen
- Fallbeispiele und Use-Cases
- Datenbankeigenschaften und Features
- Vektorisierte Inhalte für Semantic Search

### 2. PostgreSQL - Metadaten und Struktur
**Verantwortung**: Strukturelle Daten und Beziehungen

- Benutzerprofile und Preferences
- Anfrageverläufe und Kontext
- Bewertungen und Feedback
- Datenbankvergleiche und Rankings

### 3. Redis - Cache und Echtzeit
**Verantwortung**: Performance und Zustandsverwaltung

- Query-Cache für häufige Anfragen
- Session-Management
- Aktive Benutzer-Kontext
- Rate-Limiting
- Leaderboards und Statistiken

## Datenfluss

```
1. Benutzeranfrage erfasst
   ↓
2. Redis: Session-Daten laden
   ↓
3. PostgreSQL: Benutzerhistorie und Filter abrufen
   ↓
4. MongoDB: Relevante Inhalte durchsuchen
   ↓
5. Vector-Embedding: Semantische Ähnlichkeit berechnen
   ↓
6. Redis: Ergebnisse für zukünftige Anfragen cachen
   ↓
7. Empfehlungen generieren
```

## Konsistenzmodell

- **Redis**: Eventual Consistency (TTL-basiert)
- **MongoDB**: Loose Consistency (Replica Sets für Redundanz)
- **PostgreSQL**: Strong Consistency (ACID-Transaktionen)

Die Systeme sind absichtlich **entkoppelt** - jede Datenbank ist für ihre Domäne optimiert, mit klaren Grenzen und minimaler direkter Abhängigkeit.
