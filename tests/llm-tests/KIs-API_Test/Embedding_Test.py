import uuid
import datetime
import json
from sentence_transformers import SentenceTransformer

# Nutze ein sehr gutes Retrieval-Embedding-Modell
MODEL_NAME = "intfloat/e5-base-v2"  # oder "all-MiniLM-L6-v2" für ein schnelleres Modell
EMBEDDING_VERSION = "v1"
model = SentenceTransformer(MODEL_NAME)

# Beispiel-Daten: Chunks, z. B. aus MongoDB mit IDs und Quelldokumenten
chunks = [
    {
        "chunk_id": "c1a7f123-4bd2-41e9-8f88-4ca8ec104001",
        "source_document_id": "d903c121-ab33-45a8-aaa5-bbe82885f501",
        "content": "Das ist Chunk Nummer eins mit Informationen über Embeddings.",
    },
    {
        "chunk_id": "c2b8123e-7bd3-47e9-8238-7bd822192002",
        "source_document_id": "d903c121-ab33-45a8-aaa5-bbe82885f501",
        "content": "Chunk zwei behandelt die Anwendung von RAG und KI-basierten Retrieval-Systemen.",
    },
    # ... weitere Chunks
]

results = []
now_iso = datetime.datetime.utcnow().isoformat()

for chunk in chunks:
    # E5-Methode: "passage: text"
    text_to_embed = f"passage: {chunk['content']}"
    embedding = model.encode(text_to_embed).tolist()  # Wandelt in Liste für JSON

    result = {
        "id": str(uuid.uuid4()),
        "chunk_id": chunk["chunk_id"],
        "source_document_id": chunk.get("source_document_id"),
        "embedding": embedding,
        "created_at": now_iso,
        "model_name": MODEL_NAME,
        "embedding_version": EMBEDDING_VERSION
    }
    results.append(result)

# Als JSON-String speichern oder ausgeben
with open("chunk_embeddings.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Ausgabe zur Kontrolle
print(json.dumps(results, indent=2, ensure_ascii=False))
