# RAG Experiment Report
**Datum:** 2025-11-28 11:38:21
**Query:** `Was mache ich wenn ich einen Netzwerk Timeout habe?`
------------------------------------------------------------

## Testkonfiguration: Naive (Schlecht)
* **Chunk Size:** 150
* **Overlap:** 0
* **Top-K:** 5
* **Generierte Chunks:** 6 (Dauer: 0.0010s)

### Retrieval Ergebnisse:
**1. Treffer** (Sec: `N/A` | Pos: `3`)
> "ie 'batch_size' in der config.yaml auf 8.  ### 2.2 Netzwerk-Timeout Bei Timeouts..."
**2. Treffer** (Sec: `N/A` | Pos: `5`)
> "n Sie sich an support@example.com für Rückfragen...."
**3. Treffer** (Sec: `N/A` | Pos: `2`)
> "üssen vor dem Start gesetzt werden.  ## 2. Fehlerbehebung ### 2.1 Speicherfehler..."
**4. Treffer** (Sec: `N/A` | Pos: `4`)
> "die Firewall-Einstellungen Port 8080.  ## 3. Garantiebedingungen Die Garantie de..."
**5. Treffer** (Sec: `N/A` | Pos: `1`)
> "chain-community faiss-cpu sentence-transformers langchain-huggingface. Stellen S..."
----------------------------------------

## Testkonfiguration: Rekursiv (Standard)
* **Chunk Size:** 300
* **Overlap:** 60
* **Top-K:** 5
* **Generierte Chunks:** 5 (Dauer: 0.0000s)

### Retrieval Ergebnisse:
**1. Treffer** (Sec: `N/A` | Pos: `3`)
> "### 2.2 Netzwerk-Timeout Bei Timeouts erhöhen Sie den 'timeout' Parameter auf 30..."
**2. Treffer** (Sec: `N/A` | Pos: `4`)
> "## 3. Garantiebedingungen Die Garantie deckt nur Softwarefehler ab. Hardwareprob..."
**3. Treffer** (Sec: `N/A` | Pos: `2`)
> "## 2. Fehlerbehebung ### 2.1 Speicherfehler Wenn der Speicher vollläuft, prüfen ..."
**4. Treffer** (Sec: `N/A` | Pos: `1`)
> "## 1. Installation Um das System zu installieren, nutzen Sie: pip install langch..."
**5. Treffer** (Sec: `N/A` | Pos: `0`)
> "# RAG System Dokumentation Version: 1.0.2 Datum: 2023-10-27..."
----------------------------------------

## Testkonfiguration: Heading Aware (Strukturiert)
* **Chunk Size:** 0
* **Overlap:** 0
* **Top-K:** 5
* **Generierte Chunks:** 5 (Dauer: 0.0000s)

### Retrieval Ergebnisse:
**1. Treffer** (Sec: `2. Fehlerbehebung` | Pos: `3`)
> "Bei Timeouts erhöhen Sie den 'timeout' Parameter auf 30 Sekunden. Prüfen Sie auc..."
**2. Treffer** (Sec: `3. Garantiebedingungen` | Pos: `4`)
> "Die Garantie deckt nur Softwarefehler ab. Hardwareprobleme sind ausgeschlossen. ..."
**3. Treffer** (Sec: `2. Fehlerbehebung` | Pos: `2`)
> "Wenn der Speicher vollläuft, prüfen Sie die Batch-Size. Reduzieren Sie 'batch_si..."
**4. Treffer** (Sec: `1. Installation` | Pos: `1`)
> "Um das System zu installieren, nutzen Sie: pip install langchain langchain-commu..."
**5. Treffer** (Sec: `N/A` | Pos: `0`)
> "Version: 1.0.2 Datum: 2023-10-27..."
----------------------------------------
