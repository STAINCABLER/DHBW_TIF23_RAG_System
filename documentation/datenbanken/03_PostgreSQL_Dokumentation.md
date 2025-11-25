# PostgreSQL - Relationale Datenbank

## Zweck im RAG-System

PostgreSQL speichert alle **strukturierten, relationalen Daten** mit ACID-Garantien. Es ist das Rückgrat für Metadaten, Benutzerkontext und Feedback.

## Datenbankschema

### Tabellen

#### 1. `users`
Benutzerprofile und Authentifizierung.

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  profile_type ENUM('student', 'professional', 'researcher') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  preferences JSONB
);
```

#### 2. `queries`
Erfassung aller Benutzerabfragen für Kontext und Verbesserungen.

```sql
CREATE TABLE queries (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  query_text TEXT NOT NULL,
  query_parameters JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  session_id UUID,
  ip_address INET
);

CREATE INDEX idx_queries_user_id ON queries(user_id);
CREATE INDEX idx_queries_created_at ON queries(created_at DESC);
```

#### 3. `recommendations`
Generierte Empfehlungen mit Scores und Rankings.

```sql
CREATE TABLE recommendations (
  id SERIAL PRIMARY KEY,
  query_id INTEGER NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recommended_database VARCHAR(100) NOT NULL,
  match_score DECIMAL(3, 2),
  rank_position INTEGER,
  reasoning TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recommendations_query_id ON recommendations(query_id);
CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);
```

#### 4. `user_feedback`
Feedback und Ratings für Empfehlungen.

```sql
CREATE TABLE user_feedback (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  recommendation_id INTEGER REFERENCES recommendations(id) ON DELETE SET NULL,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  is_helpful BOOLEAN,
  comment TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_user_id ON user_feedback(user_id);
CREATE INDEX idx_feedback_created_at ON user_feedback(created_at DESC);
```

#### 5. `database_requirements`
Strukturierte Anforderungen für Datenbankauswahl.

```sql
CREATE TABLE database_requirements (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  scale ENUM('small', 'medium', 'large', 'enterprise') NOT NULL,
  query_pattern ENUM('oltp', 'olap', 'mixed', 'streaming') NOT NULL,
  consistency_requirement ENUM('strong', 'eventual', 'causal') NOT NULL,
  latency_requirement INTEGER, -- in milliseconds
  throughput_requirement INTEGER, -- operations per second
  data_volume_gb BIGINT,
  priority_attributes TEXT[] -- array of priorities
);
```

#### 6. `database_comparisons`
Strukturierte Vergleiche zwischen Datenbanksystemen.

```sql
CREATE TABLE database_comparisons (
  id SERIAL PRIMARY KEY,
  database_a VARCHAR(100) NOT NULL,
  database_b VARCHAR(100) NOT NULL,
  criteria_name VARCHAR(255) NOT NULL,
  score_a DECIMAL(3, 2),
  score_b DECIMAL(3, 2),
  explanation TEXT,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_db_comparisons_databases ON database_comparisons(database_a, database_b);
```

#### 7. `audit_log`
Audit-Trail für alle Systemaktivitäten.

```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  action VARCHAR(255) NOT NULL,
  entity_type VARCHAR(100),
  entity_id INTEGER,
  old_values JSONB,
  new_values JSONB,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);
```

## Views für häufige Abfragen

### Benutzerpräferenzen mit Abfrageverläufen
```sql
CREATE VIEW user_query_history AS
SELECT 
  u.id as user_id,
  u.username,
  COUNT(q.id) as total_queries,
  MAX(q.created_at) as last_query,
  AVG(r.match_score) as avg_match_score
FROM users u
LEFT JOIN queries q ON u.id = q.user_id
LEFT JOIN recommendations r ON q.id = r.query_id
GROUP BY u.id;
```

### Top empfohlene Datenbanken
```sql
CREATE VIEW top_recommendations AS
SELECT 
  recommended_database,
  COUNT(*) as recommendation_count,
  AVG(match_score) as avg_score,
  SUM(CASE WHEN uf.is_helpful THEN 1 ELSE 0 END) as helpful_count
FROM recommendations r
LEFT JOIN user_feedback uf ON r.id = uf.recommendation_id
GROUP BY recommended_database
ORDER BY helpful_count DESC;
```

## Indexing-Strategie

```sql
-- Foreign Key Indizes (automatisch erstellt)
CREATE INDEX idx_queries_user_id ON queries(user_id);
CREATE INDEX idx_recommendations_query_id ON recommendations(query_id);

-- Zeitbasierte Abfragen
CREATE INDEX idx_queries_created_at ON queries(created_at DESC);
CREATE INDEX idx_feedback_created_at ON user_feedback(created_at DESC);

-- Volltextsuche
CREATE INDEX idx_query_text ON queries USING GIN(to_tsvector('german', query_text));

-- Kombinierte Indizes für häufige Filter
CREATE INDEX idx_recommendations_user_score ON recommendations(user_id, match_score DESC);
```

## Transaktional-sichere Operationen

### Empfehlung speichern mit Feedback-Tracking
```sql
BEGIN;
  INSERT INTO queries (user_id, query_text, query_parameters, session_id)
  VALUES ($1, $2, $3, $4)
  RETURNING id INTO query_id;
  
  INSERT INTO recommendations (query_id, user_id, recommended_database, match_score, reasoning)
  VALUES (query_id, $1, $5, $6, $7);
COMMIT;
```

## Skalierungsüberlegungen

- **Partitionierung**: `queries` und `recommendations` nach Datum (monatlich)
- **Archivierung**: Alte Daten nach 1 Jahr in Archive-Tabellen verschieben
- **Read Replicas**: Für Reporting und Analytics
- **Connection Pooling**: PgBouncer oder pgpool für hohen Durchsatz
- **VACUUM & ANALYZE**: Regelmäßige Maintenance

## Performance-Tipps

- JSONB für flexible Metadaten verwenden
- Partitionierung für großvolumige Tabellen
- Column Statistics für Query Optimizer aktualisieren
- Prepared Statements für Sicherheit und Performance
- Explizite Transaktionen für Datenintegrität
