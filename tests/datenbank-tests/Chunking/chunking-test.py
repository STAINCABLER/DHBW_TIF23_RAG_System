import time
import uuid
from typing import List, Dict

# LangChain Imports
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# --- 1. SETUP: Dummy Daten & Embedding Modell ---

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

print("Lade Embedding Modell...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# --- 2. CHUNKING STRATEGIEN ---

def strategy_fixed_size(text: str, chunk_size: int, overlap: int) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=[""], 
        keep_separator=False
    )
    return splitter.create_documents([text])

def strategy_recursive(text: str, chunk_size: int, overlap: int) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.create_documents([text])

def strategy_heading_aware(text: str, chunk_size: int = 0, overlap: int = 0) -> List[Document]:
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    return markdown_splitter.split_text(text)

# --- 3. METADATA ENRICHMENT ---

def enrich_metadata(docs: List[Document], doc_name: str, version: str) -> List[Document]:
    for i, doc in enumerate(docs):
        doc.metadata["chunk_id"] = str(uuid.uuid4())
        doc.metadata["doc_id"] = doc_name
        doc.metadata["version"] = version
        doc.metadata["chunk_number"] = i
        doc.metadata["produkt"] = "RAG-Core-Enterprise"
    return docs

# --- 4. DAS LABOR-EXPERIMENT MIT DATEI-OUTPUT ---

def run_experiment(query: str, configurations: list):
    output_file = "results.md"
    
    # "w" Modus sorgt dafür, dass die Datei jedes Mal neu überschrieben wird
    with open(output_file, "w", encoding="utf-8") as f:
        
        # Helper: Schreibt gleichzeitig in Konsole UND Datei
        def log(text=""):
            print(text)
            f.write(text + "\n")

        log(f"# RAG Experiment Report")
        log(f"**Datum:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"**Query:** `{query}`")
        log("-" * 60)

        for config in configurations:
            name = config["name"]
            size = config.get("size", 0)
            overlap = config.get("overlap", 0)
            k_param = config["k"]
            strategy_func = config["strategy"]

            log(f"\n## Testkonfiguration: {name}")
            log(f"* **Chunk Size:** {size}")
            log(f"* **Overlap:** {overlap}")
            log(f"* **Top-K:** {k_param}")
            
            # 1. Chunking
            start_time = time.time()
            if name == "Heading Aware (Strukturiert)":
                 # Spezialfall für Heading Aware (ignoriert size/overlap)
                 chunks = strategy_func(raw_text)
            else:
                chunks = strategy_func(raw_text, size, overlap)
            
            # 2. Metadaten anreichern
            chunks = enrich_metadata(chunks, "Manual_v1", "1.0.2")
            
            chunking_time = time.time() - start_time
            log(f"* **Generierte Chunks:** {len(chunks)} (Dauer: {chunking_time:.4f}s)")

            # 3. Indexierung
            vectorstore = FAISS.from_documents(chunks, embeddings)
            
            # 4. Retrieval
            retriever = vectorstore.as_retriever(search_kwargs={"k": k_param})
            retrieved_docs = retriever.invoke(query)
            
            # 5. Output
            log("\n### Retrieval Ergebnisse:")
            for i, doc in enumerate(retrieved_docs):
                content_snippet = doc.page_content.replace('\n', ' ')[:80]
                header_info = doc.metadata.get('Header 2', 'N/A')
                pos_info = doc.metadata.get('chunk_number')
                
                log(f"**{i+1}. Treffer** (Sec: `{header_info}` | Pos: `{pos_info}`)")
                log(f"> \"{content_snippet}...\"")
            
            log("-" * 40)
            
    print(f"\n[INFO] Ergebnisse wurden in '{output_file}' gespeichert.")

# --- MAIN ---

if __name__ == "__main__":
    experiment_configs = [
        # {
        #     "name": "Naive (Schlecht)",
        #     "strategy": strategy_fixed_size,
        #     "size": 150,
        #     "overlap": 0,
        #     "k": 5
        # },
        # {
        #     "name": "Rekursiv (Standard)",
        #     "strategy": strategy_recursive,
        #     "size": 300,
        #     "overlap": 60,
        #     "k": 5
        # },
        {
            "name": "Heading Aware (Strukturiert)",
            "strategy": strategy_heading_aware,
            "size": 0,
            "overlap": 0,
            "k": 5
        }
    ]

    test_query = "Was mache ich wenn ich einen Netzwerk Timeout habe?"
    
    run_experiment(test_query, experiment_configs)