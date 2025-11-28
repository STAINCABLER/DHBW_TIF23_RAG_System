import time
import uuid
from typing import List, Dict

# LangChain Imports für Splitter und Vektorstore
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# --- 1. SETUP: Dummy Daten & Embedding Modell ---

# Ein Dummy-Text, der Markdown-Strukturen nutzt (für Heading-Awareness)
raw_text = """
# RAG System Dokumentation
Version: 1.0.2
Datum: 2023-10-27

## 1. Installation
Um das System zu installieren, nutzen Sie: pip install langchain langchain-community faiss-cpu sentence-transformers langchain-huggingface.
Stellen Sie sicher, dass Python 3.11+ installiert ist.
Die Umgebungsvariablen müssen vor dem Start gesetzt werden.

## 2. Fehlerbehebung
### 2.1 Speicherfehler
Wenn der Speicher vollläuft, prüfen Sie die Batch-Size. 
Reduzieren Sie 'batch_size' in der config.yaml auf 8.

### 2.2 Netzwerk-Timeout
Bei Timeouts erhöhen Sie den 'timeout' Parameter auf 30 Sekunden.
Prüfen Sie auch die Firewall-Einstellungen Port 8080.

## 3. Garantiebedingungen
Die Garantie deckt nur Softwarefehler ab. Hardwareprobleme sind ausgeschlossen.
Wenden Sie sich an support@example.com für Rückfragen.
"""

# Wir nutzen ein kleines, lokales Embedding-Modell (schnell für Tests)
print("Lade Embedding Modell...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# --- 2. CHUNKING STRATEGIEN (Implementierung Section 3 & 4) ---

def strategy_fixed_size(text: str, chunk_size: int, overlap: int) -> List[Document]:
    """
    Simuliert die 'schlechte' Strategie: Einfach nach Zeichen/Token schneiden.
    Nutzt RecursiveCharacterTextSplitter, aber mit harten Cuts, um das Problem zu zeigen.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=[""], # Force hard cut (simuliert naive Strategie)
        keep_separator=False
    )
    docs = splitter.create_documents([text])
    return docs

def strategy_recursive(text: str, chunk_size: int, overlap: int) -> List[Document]:
    """
    Gute Strategie A: Absatz-basiert / Rekursiv.
    Versucht an logischen Grenzen (Absätze, Sätze) zu trennen.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""], # Priorisiert Absätze
    )
    docs = splitter.create_documents([text])
    return docs

def strategy_heading_aware(text: str, chunk_size: int = 0, overlap: int = 0) -> List[Document]:
    """
    Gute Strategie B: Heading-aware Chunking.
    Akzeptiert chunk_size/overlap als Dummy-Argumente, um kompatibel mit der Loop zu bleiben.
    """
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    # Beachte: markdown_splitter.split_text erwartet nur den Text!
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    docs = markdown_splitter.split_text(text)
    return docs

# --- 3. METADATA ENRICHMENT (Implementierung "Warum jeder Chunk eine Rückverbindung braucht") ---

def enrich_metadata(docs: List[Document], doc_name: str, version: str) -> List[Document]:
    """
    Fügt die essentiellen Metadaten hinzu, damit der Chunk nicht 'wertlos' ist.
    """
    for i, doc in enumerate(docs):
        # Basis-Metadaten
        doc.metadata["chunk_id"] = str(uuid.uuid4())
        doc.metadata["doc_id"] = doc_name
        doc.metadata["version"] = version
        doc.metadata["chunk_number"] = i
        
        # Hinweis: Bei Heading-Aware Chunking sind die Header bereits automatisch 
        # in doc.metadata durch LangChain eingefügt worden!
        
        # Simuliere 'Produkt'-Metadaten
        doc.metadata["produkt"] = "RAG-Core-Enterprise"
        
    return docs

# --- 4. DAS LABOR-EXPERIMENT (Implementierung Section 7) ---

def run_experiment(query: str, configurations: list):
    print(f"\n{'='*60}")
    print(f"EXPERIMENT START: Query = '{query}'")
    print(f"{'='*60}")

    for config in configurations:
        name = config["name"]
        size = config.get("size", 0)
        overlap = config.get("overlap", 0)
        k_param = config["k"]
        strategy_func = config["strategy"]

        print(f"\n--- Teste Konfiguration: {name} (Size: {size}, Overlap: {overlap}, K: {k_param}) ---")
        
        # 1. Chunking
        start_time = time.time()
        if name == "Heading Aware":
            chunks = strategy_func(raw_text)
        else:
            chunks = strategy_func(raw_text, size, overlap)
        
        # 2. Metadaten anreichern
        chunks = enrich_metadata(chunks, "Manual_v1", "1.0.2")
        
        chunking_time = time.time() - start_time
        print(f"-> Generierte Chunks: {len(chunks)} (Dauer: {chunking_time:.4f}s)")

        # 3. Indexierung (Vektor Store bauen)
        # HNSW Simulation via FAISS
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
        # 4. Retrieval Simulation
        retriever = vectorstore.as_retriever(search_kwargs={"k": k_param})
        retrieved_docs = retriever.invoke(query)
        
        # 5. Ergebnis-Analyse (Output für manuelles "Eyeballing")
        print(f"-> Retrieval Ergebnisse (Top {k_param}):")
        for i, doc in enumerate(retrieved_docs):
            content_snippet = doc.page_content.replace('\n', ' ')[:80]
            # Hier prüfen wir, ob Metadaten vorhanden sind (Wichtig für Punkt "Rückverbindung")
            meta_info = f"Sec: {doc.metadata.get('Header 2', 'N/A')} | Pos: {doc.metadata.get('chunk_number')}"
            print(f"   {i+1}. [{meta_info}] {content_snippet}...")

# --- MAIN ---

if __name__ == "__main__":
    # Experiment-Konfigurationen laut Aufgabe Section 7
    experiment_configs = [
        {
            "name": "Naive (Schlecht)",
            "strategy": strategy_fixed_size,
            "size": 150,
            "overlap": 0, # Kein Overlap -> Gefahr von Satzabbrüchen
            "k": 5
        },
        {
            "name": "Rekursiv (Standard)",
            "strategy": strategy_recursive,
            "size": 300,
            "overlap": 60, # ~20% Overlap
            "k": 5
        },
        {
            "name": "Heading Aware (Strukturiert)",
            "strategy": strategy_heading_aware,
            "size": 0, # Wird hier ignoriert, da durch Header bestimmt
            "overlap": 0,
            "k": 5
        }
    ]

    # Test-Query (Sollte in Section 2 "Fehlerbehebung" gefunden werden)
    test_query = "Was mache ich wenn ich einen Netzwerk Timeout habe?"
    
    run_experiment(test_query, experiment_configs)