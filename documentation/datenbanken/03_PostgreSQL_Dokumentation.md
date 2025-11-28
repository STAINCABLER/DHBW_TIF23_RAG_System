# PostgreSQL - Relationale Datenbank

## Zweck im RAG-System

PostgreSQL speichert alle **strukturierten, relationalen Daten** mit ACID-Garantien. Es ist das Rückgrat für Metadaten, Benutzerkontext, Chat-Verwaltung und Feedback.

## Datenbankschema

### Tabellen

#### 1. `users`
Benutzerprofile und Authentifizierung.

```

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

#### 2. `conversations`
Bündelung von Nachrichten zu Chat-Sitzungen.

```

CREATE TABLE conversations (
conversation_id SERIAL PRIMARY KEY,
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
title VARCHAR(255),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);

```

#### 3. `messages`
Einzelne Nutzer- und System-Nachrichten innerhalb von Conversations.

```

CREATE TABLE messages (
message_id SERIAL PRIMARY KEY,
conversation_id INTEGER NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
content TEXT NOT NULL,
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
metadata JSONB
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, timestamp);
CREATE INDEX idx_messages_user ON messages(user_id);

```

#### 4. `uploaded_files`
Referenzen zu hochgeladenen Dokumenten für RAG-Verarbeitung.

```

CREATE TABLE uploaded_files (
file_id SERIAL PRIMARY KEY,
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
conversation_id INTEGER REFERENCES conversations(conversation_id) ON DELETE SET NULL,
original_filename VARCHAR(255) NOT NULL,
file_path TEXT NOT NULL,
file_size BIGINT NOT NULL,
file_type VARCHAR(50) NOT NULL,
is_processed BOOLEAN DEFAULT FALSE,
uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_files_user ON uploaded_files(user_id);
CREATE INDEX idx_files_conversation ON uploaded_files(conversation_id);
CREATE INDEX idx_files_processed ON uploaded_files(is_processed);

```

#### 5. `queries`
Erfassung aller Benutzerabfragen für Kontext und Verbesserungen.

```

CREATE TABLE queries (
id SERIAL PRIMARY KEY,
user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
conversation_id INTEGER REFERENCES conversations(conversation_id) ON DELETE SET NULL,
query_text TEXT NOT NULL,
query_parameters JSONB,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
session_id UUID,
ip_address INET
);

CREATE INDEX idx_queries_user_id ON queries(user_id);
CREATE INDEX idx_queries_conversation ON queries(conversation_id);
CREATE INDEX idx_queries_created_at ON queries(created_at DESC);

```

#### 6. `recommendations`
Generierte Empfehlungen mit Scores und Rankings.

```

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

#### 7. `user_feedback`
Feedback und Ratings für Empfehlungen.

```

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

#### 8. `database_requirements`
Strukturierte Anforderungen für Datenbankauswahl.

```

CREATE TABLE database_requirements (
id SERIAL PRIMARY KEY,
name VARCHAR(255) NOT NULL,
scale ENUM('small', 'medium', 'large', 'enterprise') NOT NULL,
query_pattern ENUM('oltp', 'olap', 'mixed', 'streaming') NOT NULL,
consistency_requirement ENUM('strong', 'eventual', 'causal') NOT NULL,
latency_requirement INTEGER,
throughput_requirement INTEGER,
data_volume_gb BIGINT,
priority_attributes TEXT[]
);

```

#### 9. `database_comparisons`
Strukturierte Vergleiche zwischen Datenbanksystemen.

```

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

#### 10. `audit_log`
Audit-Trail für alle Systemaktivitäten.

```

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

### Chat-Historie mit Nachrichtenanzahl
```

CREATE VIEW conversation_summary AS
SELECT
c.conversation_id,
c.user_id,
c.title,
COUNT(m.message_id) as message_count,
MAX(m.timestamp) as last_message_at,
c.created_at
FROM conversations c
LEFT JOIN messages m ON c.conversation_id = m.conversation_id
GROUP BY c.conversation_id;

```

### Benutzerpräferenzen mit Abfrageverläufen
```

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
```

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

```

-- Foreign Key Indizes
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, timestamp);
CREATE INDEX idx_queries_user_id ON queries(user_id);
CREATE INDEX idx_recommendations_query_id ON recommendations(query_id);

-- Zeitbasierte Abfragen
CREATE INDEX idx_queries_created_at ON queries(created_at DESC);
CREATE INDEX idx_feedback_created_at ON user_feedback(created_at DESC);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);

-- Volltextsuche
CREATE INDEX idx_query_text ON queries USING GIN(to_tsvector('german', query_text));
CREATE INDEX idx_message_content ON messages USING GIN(to_tsvector('german', content));

-- Kombinierte Indizes für häufige Filter
CREATE INDEX idx_recommendations_user_score ON recommendations(user_id, match_score DESC);

-- JSONB-Indizes
CREATE INDEX idx_messages_metadata ON messages USING GIN(metadata);

```

## Transaktional-sichere Operationen

### Neue Conversation mit erster Nachricht erstellen
```

BEGIN;
INSERT INTO conversations (user_id, title)
VALUES (\$1, \$2)
RETURNING conversation_id INTO conv_id;

INSERT INTO messages (conversation_id, user_id, role, content)
VALUES (conv_id, \$1, 'user', \$3);
COMMIT;

```

### Empfehlung speichern mit Feedback-Tracking
```

BEGIN;
INSERT INTO queries (user_id, conversation_id, query_text, query_parameters, session_id)
VALUES (\$1, \$2, \$3, \$4, \$5)
RETURNING id INTO query_id;

INSERT INTO recommendations (query_id, user_id, recommended_database, match_score, reasoning)
VALUES (query_id, \$1, \$6, \$7, \$8);
COMMIT;

```

## Skalierungsüberlegungen

- **Partitionierung**: `queries`, `messages` und `recommendations` nach Datum (monatlich)
- **Archivierung**: Alte Conversations nach 1 Jahr in Archive-Tabellen verschieben
- **Read Replicas**: Für Reporting und Analytics
- **Connection Pooling**: PgBouncer oder pgpool für hohen Durchsatz
- **VACUUM & ANALYZE**: Regelmäßige Maintenance

## Performance-Tipps

- JSONB für flexible Metadaten verwenden (z.B. in `messages.metadata`)
- Partitionierung für großvolumige Tabellen (`messages`, `queries`)
- Column Statistics für Query Optimizer aktualisieren
- Prepared Statements für Sicherheit und Performance
- Explizite Transaktionen für Datenintegrität
- `updated_at` Trigger für `conversations` bei neuen Messages
