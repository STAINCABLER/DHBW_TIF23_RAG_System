# RAG Experiment Report
**Datum:** 2025-12-08 11:14:13
**Query:** `Was mache ich wenn ich einen Netzwerk Timeout habe?`
------------------------------------------------------------

## Testkonfiguration: Naive (Schlecht)
* **Chunk Size:** 150
* **Overlap:** 0
* **Top-K:** 5
* **Generierte Chunks:** 6 (Dauer: 0.0053s)

### Retrieval Ergebnisse:
**1. Treffer** (Sec: `N/A` | Pos: `3`)
> "ie 'batch_size' in der config.yaml auf 8.  ### 2.2 Netzwerk-Timeout Bei Timeouts erhöhen Sie den 'timeout' Parameter auf 30 Sekunden. Prüfen Sie auch"
**2. Treffer** (Sec: `N/A` | Pos: `5`)
> "n Sie sich an support@example.com für Rückfragen."
**3. Treffer** (Sec: `N/A` | Pos: `2`)
> "üssen vor dem Start gesetzt werden.  ## 2. Fehlerbehebung ### 2.1 Speicherfehler Wenn der Speicher vollläuft, prüfen Sie die Batch-Size.  Reduzieren S"
**4. Treffer** (Sec: `N/A` | Pos: `4`)
> "die Firewall-Einstellungen Port 8080.  ## 3. Garantiebedingungen Die Garantie deckt nur Softwarefehler ab. Hardwareprobleme sind ausgeschlossen. Wende"
**5. Treffer** (Sec: `N/A` | Pos: `1`)
> "chain-community faiss-cpu sentence-transformers langchain-huggingface. Stellen Sie sicher, dass Python 3.11+ installiert ist. Die Umgebungsvariablen m"
----------------------------------------

## Testkonfiguration: Rekursiv (Standard)
* **Chunk Size:** 300
* **Overlap:** 60
* **Top-K:** 5
* **Generierte Chunks:** 5 (Dauer: 0.0004s)

### Retrieval Ergebnisse:
**1. Treffer** (Sec: `N/A` | Pos: `3`)
> "### 2.2 Netzwerk-Timeout Bei Timeouts erhöhen Sie den 'timeout' Parameter auf 30 Sekunden. Prüfen Sie auch die Firewall-Einstellungen Port 8080."
**2. Treffer** (Sec: `N/A` | Pos: `4`)
> "## 3. Garantiebedingungen Die Garantie deckt nur Softwarefehler ab. Hardwareprobleme sind ausgeschlossen. Wenden Sie sich an support@example.com für Rückfragen."
**3. Treffer** (Sec: `N/A` | Pos: `2`)
> "## 2. Fehlerbehebung ### 2.1 Speicherfehler Wenn der Speicher vollläuft, prüfen Sie die Batch-Size.  Reduzieren Sie 'batch_size' in der config.yaml auf 8."
**4. Treffer** (Sec: `N/A` | Pos: `1`)
> "## 1. Installation Um das System zu installieren, nutzen Sie: pip install langchain langchain-community faiss-cpu sentence-transformers langchain-huggingface. Stellen Sie sicher, dass Python 3.11+ installiert ist. Die Umgebungsvariablen müssen vor dem Start gesetzt werden."
**5. Treffer** (Sec: `N/A` | Pos: `0`)
> "# RAG System Dokumentation Version: 1.0.2 Datum: 2023-10-27"
----------------------------------------

## Testkonfiguration: Heading Aware (Strukturiert)
* **Chunk Size:** 0
* **Overlap:** 0
* **Top-K:** 5
* **Generierte Chunks:** 5 (Dauer: 0.0000s)

### Retrieval Ergebnisse:
**1. Treffer** (Sec: `2. Fehlerbehebung` | Pos: `3`)
> "Bei Timeouts erhöhen Sie den 'timeout' Parameter auf 30 Sekunden. Prüfen Sie auch die Firewall-Einstellungen Port 8080."
**2. Treffer** (Sec: `3. Garantiebedingungen` | Pos: `4`)
> "Die Garantie deckt nur Softwarefehler ab. Hardwareprobleme sind ausgeschlossen. Wenden Sie sich an support@example.com für Rückfragen."
**3. Treffer** (Sec: `2. Fehlerbehebung` | Pos: `2`)
> "Wenn der Speicher vollläuft, prüfen Sie die Batch-Size. Reduzieren Sie 'batch_size' in der config.yaml auf 8."
**4. Treffer** (Sec: `1. Installation` | Pos: `1`)
> "Um das System zu installieren, nutzen Sie: pip install langchain langchain-community faiss-cpu sentence-transformers langchain-huggingface. Stellen Sie sicher, dass Python 3.11+ installiert ist. Die Umgebungsvariablen müssen vor dem Start gesetzt werden."
**5. Treffer** (Sec: `N/A` | Pos: `0`)
> "Version: 1.0.2 Datum: 2023-10-27"
----------------------------------------
