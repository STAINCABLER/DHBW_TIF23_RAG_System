# Embedding Test Guide

## Overview

This guide explains how to set up and run `embedding-test.py`. The script generates sentence embeddings with [SentenceTransformers](https://www.sbert.net/) and stores them in a PostgreSQL table named `faq`. All progress and errors are written to `embedding-test.log` in the same directory.

## Prerequisites

- Python 3.9 or newer
- A PostgreSQL instance that you can reach from your machine
- PowerShell 5.1 (default on Windows) or a compatible shell
- Optional: virtual environment tooling such as `python -m venv`

## Environment Setup

1. Open PowerShell in `d:\Documents\GitHub\DHBW_TIF23_RAG_System\datenbank-tests\Embeddings`.
2. (Optional) Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install the required packages:
   ```powershell
   pip install sentence-transformers psycopg2-binary
   ```

## Database Preparation

1. Ensure PostgreSQL is running and reachable.
2. Create the target database if it does not exist:
   ```powershell
   psql -U postgres -c "CREATE DATABASE test;"
   ```
3. (Optional) Pre-create the `faq` table if you want to control the schema. The script will otherwise create a minimal table automatically:
   ```sql
   CREATE TABLE IF NOT EXISTS faq (
       id SERIAL PRIMARY KEY,
       question TEXT NOT NULL,
       embedding DOUBLE PRECISION[] NOT NULL
   );
   ```

## Configuration Options

- Set `EMBEDDING_DB_DSN` to override the PostgreSQL connection string. Example: `postgresql://postgres:postgres@localhost:5432/test`.
- Set `EMBEDDING_MODEL` to use a different SentenceTransformer model.
- Supply `--questions-file path\to\questions.txt` to load custom prompts. Use one question per line and prefix comment lines with `#`.

## Running The Script

Run the script from the project directory:
```powershell
python embedding-test.py
```

Optional flags:
```powershell
python embedding-test.py --dsn "postgresql://user:password@host:5432/db" --model-name all-MiniLM-L6-v2 --questions-file prompts.txt
```

## Output And Logs

- All actions and errors are written to `embedding-test.log` and echoed to the console.
- Each new question is inserted once. Existing questions are skipped to avoid duplicates.
- On success the last log line contains `Embedding test completed. Inserted X new rows.`

## Troubleshooting

- Failure to load the model usually indicates missing dependencies or an offline environment. Re-run pip install and ensure internet access for the initial model download.
- Database connection errors often stem from an incorrect DSN or network access. Test connectivity with `psql` first.
- To rerun with fresh data, delete rows from `faq` before executing the script again:
  ```powershell
  psql "postgresql://postgres:postgres@localhost:5432/test" -c "TRUNCATE faq;"
  ```
