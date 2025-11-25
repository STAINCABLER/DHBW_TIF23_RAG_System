# Redis - In-Memory Caching und Echtzeit-Datenbank

## Zweck im RAG-System

Redis dient als **Cache-Layer und Echtzeit-Datenspeicher** für hohe Performance und Zustandsverwaltung.

## Datenstrukturen und Keys

### 1. Session Management
```
KEY: session:{session_id}
TYPE: Hash
FIELDS:
  user_id: Integer
  username: String
  created_at: Timestamp
  last_activity: Timestamp
  ip_address: String
TTL: 24 hours
```

**Beispiel:**
```redis
HSET session:abc123 user_id 42 username "leon" created_at 1732532100 last_activity 1732532100
EXPIRE session:abc123 86400
```

### 2. Query Cache
```
KEY: query_cache:{query_hash}
TYPE: String (JSON)
VALUE: 
{
  "query_text": "Find database for...",
  "recommendations": [...],
  "generated_at": Timestamp,
  "hit_count": Integer
}
TTL: 1 hour (für häufige Anfragen, 30 min für seltene)
```

**Beispiel:**
```redis
SET query_cache:abc... '{"recommendations":[...]}' EX 3600
INCR query_cache:abc...:hits
```

### 3. User Context
```
KEY: user_context:{user_id}
TYPE: Hash
FIELDS:
  current_query: String
  last_recommendation: String
  preferences: JSON
  location: String
  device_type: String
TTL: 30 minutes (rolling)
```

**Beispiel:**
```redis
HSET user_context:42 current_query "scale,oltp" preferences '{"language":"de"}'
```

### 4. Feature Flags und Configuration
```
KEY: config:feature_flags
TYPE: Hash
FIELDS:
  enable_semantic_search: "true|false"
  enable_vector_embeddings: "true|false"
  enable_caching: "true|false"
```

**Beispiel:**
```redis
HSET config:feature_flags enable_semantic_search true
```

### 5. Rate Limiting
```
KEY: rate_limit:{user_id}:{endpoint}
TYPE: String (Counter)
VALUE: Request count
TTL: 1 minute (sliding window)
```

**Beispiel für 100 Requests/Minute pro User:**
```redis
INCR rate_limit:42:/api/recommend
EXPIRE rate_limit:42:/api/recommend 60
```

### 6. Recommendation Leaderboard
```
KEY: leaderboard:top_databases
TYPE: Sorted Set
MEMBERS: Database names
SCORES: Recommendation count
```

**Beispiel:**
```redis
ZADD leaderboard:top_databases 450 PostgreSQL 380 MongoDB 220 Redis
ZREVRANGE leaderboard:top_databases 0 10 WITHSCORES
```

### 7. Real-time Statistics
```
KEY: stats:{metric_name}:{time_window}
TYPE: Hash
FIELDS:
  total_queries: Integer
  avg_response_time: Float
  unique_users: Integer
  timestamp: Timestamp

Alternative: Sorted Set für zeitserienbasierte Metriken
KEY: stats_timeseries:{metric_name}
TYPE: Sorted Set
MEMBERS: Wert
SCORES: Timestamp
```

**Beispiel:**
```redis
HINCRBY stats:queries:hourly total 1
HSET stats:queries:hourly avg_response_time 125
```

### 8. Aktive Nutzer Tracking
```
KEY: active_users:{hour}
TYPE: Set
MEMBERS: User IDs
TTL: 2 hours
```

**Beispiel:**
```redis
SADD active_users:2025-11-25-14 42 43 44 45
```

### 9. Token Blacklist (für Logout)
```
KEY: token_blacklist:{token}
TYPE: String
VALUE: Boolean (presence key)
TTL: Token expiration time
```

**Beispiel:**
```redis
SET token_blacklist:exp_token_xyz "" EX 3600
```

### 10. Pending Tasks Queue
```
KEY: task_queue:{queue_name}
TYPE: List
MEMBERS: Task JSON objects
```

**Beispiel:**
```redis
LPUSH task_queue:recommendations '{"user_id":42,"query":"scale,oltp"}'
RPOP task_queue:recommendations
```

## Redis-Module und erweiterte Features

### Pub/Sub für Echtzeit-Updates
```
CHANNEL: recommendations:{user_id}
MESSAGE: Neue Empfehlung verfügbar

PUBLISH recommendations:42 '{"db":"PostgreSQL","score":0.95}'
SUBSCRIBE recommendations:42
```

### Streams für Event Log
```
KEY: event_stream:queries
TYPE: Stream
ENTRIES: {timestamp, user_id, query_text, recommendations}
```

**Beispiel:**
```redis
XADD event_stream:queries * user_id 42 query "PostgreSQL vs MongoDB" recommendations "PostgreSQL"
XREAD STREAMS event_stream:queries 0
```

### Bloom Filter für Duplikatserkennung
```
KEY: seen_queries
TYPE: Bloom Filter
PURPOSE: Schnelle Duplikatserkennung
```

**Beispiel:**
```redis
BF.ADD seen_queries "query_hash_123"
BF.EXISTS seen_queries "query_hash_123"
```

## Expiration Strategy (TTL)

| Key-Typ | TTL | Begründung |
|---------|-----|-----------|
| Session Data | 24h | Benutzer angemeldet halten |
| Query Cache (häufig) | 1h | Häufige Anfragen schnell verfügbar |
| Query Cache (selten) | 30min | Seltene Anfragen nicht zu lange lagern |
| User Context | 30min | Kontext verfällt, aber Session bleibt |
| Rate Limits | 1min | Sliding window für Requests |
| Statistics | 1h | Stündliche Aggregation |
| Active Users | 2h | Etwas Puffer für Neuverbindungen |
| Token Blacklist | Token TTL | Nur so lange wie Token gültig ist |

## Backup und Persistence

### Persistence-Optionen

**RDB (Snapshots)**
```conf
save 900 1        # Nach 900s wenn 1+ Key geändert
save 300 10       # Nach 300s wenn 10+ Keys geändert
save 60 10000     # Nach 60s wenn 10000+ Keys geändert
```

**AOF (Append Only File)**
```conf
appendonly yes
appendfsync everysec  # Disk-Sync jede Sekunde
```

### Recommended Setup
```
# Hybrid-Approach für dieses Projekt
save 3600 1       # Täglich snapshots
appendonly yes
appendfsync everysec
```

## Performance-Optimierungen

### Connection Pooling (Python)
```python
from redis import ConnectionPool
pool = ConnectionPool(host='localhost', port=6379, max_connections=50)
redis_client = redis.Redis(connection_pool=pool)
```

### Pipelining für Batch-Operationen
```python
pipe = redis_client.pipeline()
for i in range(100):
    pipe.set(f'key_{i}', f'value_{i}')
pipe.execute()
```

### Lua Scripts für atomare Operationen
```python
# Beispiel: Atomic rate limit check
script = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local current = redis.call('INCR', key)
if current == 1 then
  redis.call('EXPIRE', key, 60)
end
return current <= limit
"""
redis_client.register_script(script)
```

## Monitoring und Debugging

```redis
# Anzahl der Keys pro Datenbank
INFO keyspace

# Speichernutzung
INFO memory

# Alle Keys auflisten (Achtung: Production!)
KEYS *

# Key-Größe analysieren
MEMORY USAGE session:abc123

# Langsame Queries tracken
SLOWLOG GET 10

# Monitor in Echtzeit
MONITOR
```

## Skalierungsüberlegungen

- **Cluster Mode**: Für > 1TB Daten
- **Replication**: Master-Slave für Redundanz
- **Sentinel**: Automatisches Failover
- **Sharding**: Nach User-ID oder Session-ID
- **Eviction Policy**: `allkeys-lru` wenn Speicher voll

## Eviction Policies

```conf
# Wenn Speicher voll ist:
maxmemory-policy allkeys-lru    # Entferne Key mit ältestem Zugriff
# Alternativen:
# - allkeys-lfu: Least frequently used
# - volatile-lru: Nur Keys mit TTL
# - volatile-random: Zufällige Keys mit TTL
```
