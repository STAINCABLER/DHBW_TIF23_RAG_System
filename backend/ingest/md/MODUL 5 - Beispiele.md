# MODUL 5 Beispiele

---

## BEISPIEL 1 — Produktdokumentation (RAG-Chunks)

**Use Case:**
Ein Support-Agent fragt: „Wie resette ich das Gerät?"
Das System lädt ca. 6 relevante Chunks.

### 1.1 Access Path

- ANN-Suche liefert 6 chunk_ids.
- Für jede ID: punktuelles Lesen (find chunk by chunk_id).
- Übergabe von Text + Metadaten an das LLM.

Dieser Pfad ist kritisch, weil er direkt die Antwortqualität bestimmt.

### 1.2 Modellierungsentscheidungen

#### EMBED vs REFERENCE (Beispiel 1)

❌ **EMBED (falsch)** — Beispiel (schlechte Modellierung):

```json
{
  "doc_id": "doc_123",
  "title": "...",
  "full_text": "... großer Text ...",
  "embeddings": [
    { "chunk_id": "c1", "vec": [0.123, "..."] },
    { "chunk_id": "c2", "vec": [0.551, "..."] }
  ]
}
```

Probleme:

- riesige Dokumente
- Embeddings (256–4096 floats) machen Dokument groß
- jede Änderung eines Embedding-Modells → komplettes Dokument wird „invalidiert"
- ANN läuft ohnehin in pgvector → Mongo würde Embeds nie lesen

✔️ **REFERENCE (richtig)** — Chunk-Dokument bleibt klein, Embedding ist separat gespeichert.

#### Big Document vs Small Document (Beispiel 1)

❌ **Big Document (falsch)** — Alles in einem Dokument:

- gesamtes Manual
- alle Chunks
- alle Metadaten
- alle Embeddings

→ jedes Lesen lädt zu viel → 50–200 ms nur Daten-Transfer.

✔️ **Small Document (richtig)** — Ein Chunk = ein Dokument. Typisch 1–3 KB Text + Metadaten.

Warum?

- ANN liefert punktuelle IDs
- Query lädt genau 6 Dokumente
- ideal für Indexierung
- keine Updates → immutable → extrem performant

#### Precompute vs Compute-on-Read (Beispiel 1)

❌ **Compute-on-Read (falsch)** — Metadaten erst beim Lesevorgang extrahieren (z. B. Überschriften, Positionen).
→ erhöht Latenz im kritischen Pfad.

✔️ **Precompute (richtig)** — Beim Ingest:

- section_title
- position
- product_family
- version
- keywords

werden einmalig berechnet.

→ Retrieval ist nur noch ein reiner Lookup.

### 1.3 Finales Datenmodell

```json
{
  "chunk_id": "doc_123_05",
  "doc_id": "doc_123",
  "position": 5,
  "section_title": "Reset Vorgang",
  "text": "...",
  "keywords": ["reset", "start", "error"],
  "product_family": "KA-22",
  "version": "2024",
  "embedding_id": "emb_123_05"
}
```

Indexes:

- doc_id + position
- section_title
- product_family

### 1.4 Kritischer Pfad & Latenzen

| Variante | Latenz | Problem |
|----------|--------|---------|
| EMBED + Big Document | 50–150 ms | großes Dokument, Parsing |
| Compute-on-Read-Metadaten | +10–25 ms | unnötige CPU |
| Small + Reference + Precompute | 3–8 ms | ideal |

### 1.5 Kurzbegründung

Kleine immutable Dokumente + precomputed Metadaten + referenzierte Embeddings ergeben optimale Latenz im Chunk-Loading-Pfad.

---

## BEISPIEL 2 — Kundendaten (OLTP, Postgres)

**Use Case:**
„Kundenprofil laden + gelegentlich aktualisieren"

### 2.1 Access Path

- `SELECT * FROM customer WHERE customer_id = ?`
- gelegentlich Updates in Unterobjekten (Adresse, Verträge usw.)

Critical path: schneller Lookup + sicheres Update.

### 2.2 Modellierungsentscheidungen

#### EMBED vs REFERENCE (Beispiel 2)

❌ **EMBED (falsch)**

```json
{
  "customer_id": "C123",
  "profile": {
     "address": {"..."},
     "contracts": ["..."],
     "payments": ["..."]
  }
}
```

Probleme:

- mehrere Teilobjekte ändern sich unabhängig
- Embeds erzeugen widersprüchliche Kopien
- großes Dokument → Locks → hohe Latenz bei Updates

✔️ **REFERENCE (richtig)** — Separate Tabellen/Objekte:

- customer
- address
- contract
- payment

#### Big Document vs Small Document (Beispiel 2)

❌ **Big Document (falsch)** — Alles in einer „Kunden-Mega-Zeile" führt zu:

- 5–20 KB pro Kunde
- Updates werden teuer
- Deadlocks durch große Row-Locks

✔️ **Small Documents (richtig)** — Viele kleine Zeilen:

- Adresse separat
- Verträge separat
- Zahlungen separat

→ kleine Locks
→ schnelle Writes
→ schnelle Reads

#### Precompute vs Compute-on-Read (Beispiel 2)

✔️ **Compute-on-Read (richtig)**

Warum?

- einzelne Felder schnell verfügbar
- keine teuren Berechnungen
- Precompute unnötig
- Profile sind klein

❌ **Precompute (hier nicht sinnvoll)** — Kein Nutzen, verursacht nur Komplexität.

### 2.3 Finales Datenmodell

Postgres:

```sql
customer(customer_id PK, name, email, created_at)
address(address_id PK, customer_id FK, street, city, updated_at)
contract(contract_id PK, customer_id FK, type, status)
payment(payment_id PK, customer_id FK, amount, date)
```

### 2.4 Kritischer Pfad & Latenzen

| Variante | Latenz | Problem |
|----------|--------|---------|
| Big Document | 20–80 ms | Großes Row-Lock, unnötiger Transfer |
| EMBED | 10–40 ms | Updates blockieren Dokument |
| Referenced + Small | 2–6 ms | ideal für OLTP |

### 2.5 Kurzbegründung

OLTP braucht ACID, kleine Updates und feingranulare Struktur.
→ relationales Modell mit Referenzen ist optimal.

---

## BEISPIEL 3 — Chunks eines Dokuments (MongoDB)

(RAG-Dokumentteile, aber ohne Embedding-Aspekt)

### 3.1 Access Path

„Lade 5–10 Chunks anhand ihrer chunk_ids"

### 3.2 Modellierungsentscheidungen

#### EMBED vs REFERENCE (Beispiel 3)

❌ **EMBED (falsch)** — Das Gesamtdokument enthält alle Chunks als Liste.

```json
{
  "doc_id": "d123",
  "chunks": [
       { "id": 1, "text": "...", "section_title": "..."},
       { "id": 2, "text": "...", "section_title": "..."}
  ]
}
```

Probleme:

- Dokument wird riesig
- jeder Chunk-Read lädt alle anderen mit
- unperformant für random access

✔️ **REFERENCE (richtig)** — Chunk als eigenes Dokument.

#### Big Document vs Small Document (Beispiel 3)

❌ **Big Document (falsch)** — Gesamtes Manual in einem Objekt:
→ 100–500 KB
→ punktuelle Reads werden schlecht
→ CPU & Transferzeit steigen

✔️ **Small Document (richtig)** — Ein Chunk = ein Dokument
→ 1–3 KB → optimal für Random Reads

#### Precompute vs Compute-on-Read (Beispiel 3)

✔️ **Precompute**

- section_title
- position
- keywords

❌ **Compute-on-Read** — Aus Text extrahieren → teuer → nicht im kritischen Pfad.

### 3.3 Finales Datenmodell

```json
{
  "chunk_id": "doc_88_02",
  "doc_id": "doc_88",
  "position": 2,
  "section_title": "Installation",
  "text": "...",
  "keywords": ["install", "setup"],
  "version": "2024"
}
```

Indexes:

- doc_id, position
- section_title

### 3.4 Kritischer Pfad & Latenzen

| Modell | Latenz | Problem |
|--------|--------|---------|
| Big Document | 30–80 ms | lädt viel zu große Datenmenge |
| Compute-on-Read-Metadaten | +10–25 ms | unnötige Text-Analyse |
| Small + Precompute | 3–7 ms | optimal |

### 3.5 Kurzbegründung

Viele punktuelle Reads + große Texte → kleine, immutable Dokumente + precomputed Metadaten.

---

## BEISPIEL 4 — Chat-Historie (append-only, MongoDB)

### 4.1 Access Path

„Füge eine neue Message hinzu"

### 4.2 Modellierungsentscheidungen

#### EMBED vs REFERENCE (Beispiel 4)

✔️ **EMBED (richtig)** — Ein Chat = ein Dokument, messages = Array

```json
{
  "chat_id": "c123",
  "messages": [
     { "from": "customer", "ts": "...", "text": "..." },
     { "from": "agent", "ts": "...", "text": "..." }
  ]
}
```

Warum?

- append-only
- Access Path liest meist gesamten Verlauf
- keine komplexen Updates

❌ **REFERENCE (falsch)** — Einzelne Nachrichten als eigene Dokumente → viele Roundtrips.

#### Big Document vs Small Document (Beispiel 4)

❌ **Zu großes Dokument** — Wenn messages-Array > 1–2 MB:

- Schreiboperationen werden teuer
- Dokument muss komplett neu geschrieben werden
- Gefahr von 16-MB-Limit in Mongo

✔️ **Mittlere Größe + Split-Strategie**

- max. ~50k Messages pro Dokument
- ab Schwelle → neues Chat-Dokument anlegen
- TTL nutzbar für Ephemeral Context

#### Precompute vs Compute-on-Read (Beispiel 4)

✔️ **Precompute**

- message_count
- last_message_at

Warum?

- Listenansichten filtern häufig nach „aktive Chats"
- count() pro Anfrage teuer
- Precompute reduziert Query-Latenz massiv

❌ **Compute-on-Read** — Langsam bei großen Arrays.

### 4.3 Finales Datenmodell

```json
{
  "chat_id": "c123",
  "customer_id": "C123",
  "messages": [
     { "from": "customer", "ts": "...", "text": "..." }
  ],
  "message_count": 42,
  "last_message_at": "2025-03-01T10:00:00Z",
  "ttl": 86400
}
```

Index:

- customer_id
- last_message_at

### 4.4 Kritischer Pfad & Latenzen

| Modell | Latenz | Problem |
|--------|--------|---------|
| Referenced Messages | 10–40 ms | zu viele Einzel-Queries |
| Big Document >1 MB | 20–60 ms | Write Rewrite zu teuer |
| Embed + moderate Size + Precompute | 2–6 ms | optimal |

### 4.5 Kurzbegründung

Append-only + seltene Reads → eingebettet.
Precompute ermöglicht schnelle Listenansichten.

---

## BEISPIEL 5 — Geräte-Konfigurationsprofile (große Dokumente sind sinnvoll)

(z. B. für IoT-Geräte, Maschinen, Router, Industriesteuerungen)

**Use Case:**
Ein Techniker möchte die vollständige Konfiguration eines Geräts sehen und Änderungen als Ganzes versionieren.

**Beispiel-Frage:**
„Zeig mir die vollständige Konfiguration der Heizung H-77 und erstelle eine neue Version davon."

### 5.1 Access Path

- Techniker öffnet ein Gerät → System lädt das gesamte Config-Dokument.
- Techniker ändert wenige Werte → System speichert die neue Version komplett.
- Optional: Vergleiche Versionen (Diff).

Dieser Pfad ist kritisch, weil:

- die komplette Konfiguration auf einmal gebraucht wird,
- Teilzufgriffe keinen echten Nutzen hätten,
- Versionierbarkeit nur funktioniert, wenn das gesamte Objekt konsistent ist.

### 5.2 Modellierungsentscheidungen

#### EMBED vs REFERENCE (Beispiel 5)

❌ **REFERENCE (falsch)** — Beispiel:

```json
{
  "device_id": "H77",
  "network_settings": { "..." },
  "heating_curves_ref": "cfg1234",
  "safety_constraints_ref": "cfg777",
  "sensor_profiles_ref": "cfg881"
}
```

Probleme:

- Um die vollständige Config zu sehen → 5–10 Datenbank-Queries
- Versionskontrolle wird komplex: mehrere Objekte müssen gleichzeitig eingefroren werden
- Inkonsistenzen zwischen Teilobjekten möglich
- Latenz steigt mit jedem Sub-Query

✔️ **EMBED (richtig)** — Eine Konfiguration ist eine atomare Einheit → Änderungen immer als Ganzes.

Beispielstruktur:

- Netzwerk-Einstellungen
- Sensor-Kalibrierungen
- Parameter für Heizung/Kühlung
- Sicherheitslogik
- Firmware-Voreinstellungen

→ ein großes Konfigurationsdokument

#### Big Document vs Small Document (Beispiel 5)

❌ **Small Documents (falsch)** — Warum nicht 20 kleine Dokumente?

- Lose gekoppelte Fragmente erschweren Debugging
- Historische Vergleiche werden unmöglich → „Welche Version war aktiv am 21. März?"
- Updates müssen über viele Einzelobjekte laufen → Race Conditions
- Backup & Audit unübersichtlich
- ACID verliert an praktischer Wirkung, wenn Änderungen verteilt sind

✔️ **Big Document (richtig)** — Eine Version = 1 großes JSON (100–500 KB)
→ ideal für:

- Atomare Speicherung
- Versionierung (Archivierung pro Version)
- Audits
- Snapshot-Recovery
- Debugging
- Migrationslogik

MongoDB kann 16 MB pro Dokument → 100–500 KB sind perfekt im Sweet Spot.

#### Precompute vs Compute-on-Read (Beispiel 5)

✔️ **Precompute** — Bei der Speicherung:

- checksum (SHA-256 über das komplette JSON)
- version_number
- created_at
- created_by
- diff_to_previous (optional vorab berechnet)
- device_state_hash (aggregiert wichtige Felder)

Warum?

- Die häufigsten Queries sind → „Welche Version ist aktiv?"
- Hashes/Checksums müssen schnell überprüft werden
- Versionsvergleich (diff) wird günstiger

❌ **Compute-on-Read** — Gesamtes Dokument live zu diffen → viel zu teuer.

### 5.3 Finales Datenmodell

```json
{
  "device_id": "H77",
  "version_number": 14,
  "created_at": "2025-01-12T10:00:00Z",
  "created_by": "technician_332",
  "checksum": "d2ab3f9919...",
  "diff_to_previous": {
      "heating_curve": "changed",
      "safety.max_temp": "changed"
  },
  "config": {
    "network": {
      "ip": "192.168.1.44",
      "mask": "255.255.255.0",
      "gateway": "192.168.1.1"
    },
    "heating": {
      "curves": ["..."],
      "limits": {
          "max_temp": 75,
          "min_temp": 10
      }
    },
    "sensors": {
       "humidity": {"cal": 1.02},
       "temp": {"cal": 0.98}
    },
    "firmware": {
      "version": "3.7.2",
      "modules": {
          "security": "1.1",
          "control": "2.0"
      }
    }
  }
}
```

Indexes:

- device_id
- device_id + version_number
- checksum

Dokumentgröße typischerweise: 200–400 KB → perfekt für Config-Snapshots.

### 5.4 Kritischer Pfad & Latenzen

| Modell | Latenz | Problem |
|--------|--------|---------|
| many small documents + references | 30–150 ms | viele Roundtrips, mögliche Inkonsistenzen |
| Embedded config + mittelgroßes Dokument (200–500 KB) | 5–15 ms | ideal |
| Compute-on-Read für diff/checksum | +20–60 ms | unnötige CPU-Last |
| Precompute bei Ingest | 0 ms in Read-Pfad | ideal |

### 5.5 Kurzbegründung

Große Dokumente sind sinnvoll, wenn:

- eine Konfiguration als Ganzes geladen wird,
- Versionierung als Ganzes stattfinden muss,
- atomare Updates sinnvoll sind,
- Debugging/Audit/Compliance wichtig sind.

Ein mittelgroßes, aber komplett eingebettetes JSON (200–500 KB) ist in MongoDB für diesen Anwendungsfall perfekt:
1 Query, 1 konsistenter Snapshot, 1 Version.
