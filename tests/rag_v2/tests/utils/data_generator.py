"""
Data Generator - Generierung realistischer Testdaten
=====================================================

Dieses Modul generiert Testdaten, die den Strukturen aus den
Kursmaterialien entsprechen:

- Chunks: JSON-Dokumente mit Text, Metadaten und Embedding-Referenz
- Vektoren: Normalisierte Float-Arrays (768 Dimensionen)
- Relationale Daten: User-Profile, Logs, Metadaten

Modul-Referenz:
    - Anforderungen 3: Datenmodellierung für Tests
    - Modul 6: Chunking ist Datenmodellierung

Autor: RAG Performance Test Suite
"""

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Generator, Optional
import logging

# Optionale Imports (werden bei Bedarf geprüft)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from faker import Faker
    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False

logger = logging.getLogger(__name__)


class DataGenerator:
    """
    Generiert realistische Testdaten für die Performance-Tests.
    
    Die Datenstrukturen orientieren sich an den Modulen 5 und 6:
    - Chunks sind "Small Documents" mit Referenz-Logik
    - Vektoren sind normalisierte Embeddings
    - Relationale Daten folgen klassischen Schemata
    
    Beispiel:
        generator = DataGenerator(config)
        
        # 10.000 Chunks generieren
        chunks = list(generator.generate_chunks(10000))
        
        # 50.000 Vektoren generieren
        vectors = generator.generate_vectors(50000)
    """
    
    def __init__(self, config: dict):
        """
        Initialisiert den Data Generator.
        
        Args:
            config: Die geladene Konfiguration aus test_config.yaml
        """
        self.config = config
        general = config.get("general", {})
        
        # Konfiguration extrahieren
        self.vector_dimensions = general.get("vector_dimensions", 768)
        self.batch_size = general.get("batch_size", 1000)
        
        # Faker initialisieren (falls verfügbar)
        if HAS_FAKER:
            self.faker = Faker("de_DE")  # Deutsche Locale für realistische Daten
            Faker.seed(42)  # Reproduzierbare Ergebnisse
        else:
            self.faker = None
            logger.warning(
                "Faker nicht installiert - verwende einfache Zufallsdaten"
            )
        
        # Random Seed für Reproduzierbarkeit
        random.seed(42)
        if HAS_NUMPY:
            np.random.seed(42)
        
        # Vordefinierte Kategorien für Filterung
        self.categories = ["product_a", "product_b", "product_c", 
                          "support", "faq", "manual"]
        self.sources = ["handbook.pdf", "faq.md", "support_kb.json", 
                       "product_docs.txt"]
    
    # =========================================================================
    # Chunk-Generierung (MongoDB)
    # =========================================================================
    
    def generate_chunks(
        self, 
        count: int, 
        text_length: tuple[int, int] = (500, 1000)
    ) -> Generator[dict, None, None]:
        """
        Generiert Chunk-Dokumente für MongoDB.
        
        Struktur eines Chunks (gemäß Modul 6):
            - chunk_id: Eindeutige ID
            - text: Der eigentliche Textinhalt (500-1000 Zeichen)
            - metadata: Quelle, Seite, Kategorie
            - embedding_ref: Referenz zum Vektor-Store
            - created_at: Zeitstempel
        
        Args:
            count: Anzahl der zu generierenden Chunks
            text_length: Tuple (min, max) für Textlänge
        
        Yields:
            Dictionary mit Chunk-Daten
        """
        logger.info(f"Generiere {count} Chunks...")
        
        for i in range(count):
            chunk_id = str(uuid.uuid4())
            
            # Text generieren
            text = self._generate_text(
                random.randint(text_length[0], text_length[1])
            )
            
            # Chunk-Dokument erstellen
            chunk = {
                "_id": chunk_id,
                "chunk_id": chunk_id,
                "text": text,
                "metadata": {
                    "source": random.choice(self.sources),
                    "page": random.randint(1, 100),
                    "category": random.choice(self.categories),
                    "language": "de",
                },
                "embedding_ref": f"emb_{chunk_id}",  # Referenz zum Vektor
                "created_at": datetime.utcnow() - timedelta(
                    days=random.randint(0, 365)
                ),
                "word_count": len(text.split()),
            }
            
            yield chunk
    
    def generate_chunk_batch(
        self, 
        count: int
    ) -> list[dict]:
        """
        Generiert eine Liste von Chunks (für Bulk-Insert).
        
        Args:
            count: Anzahl der Chunks
        
        Returns:
            Liste von Chunk-Dictionaries
        """
        return list(self.generate_chunks(count))
    
    # =========================================================================
    # Vektor-Generierung (pgvector / MongoDB Vector)
    # =========================================================================
    
    def generate_vectors(
        self, 
        count: int,
        normalize: bool = True
    ) -> list[dict]:
        """
        Generiert Vektor-Dokumente für die Vektorsuche.
        
        Struktur eines Vektor-Dokuments (gemäß Modul 7):
            - embedding_id: Referenz zum Chunk
            - vector: Float-Array (768 Dimensionen)
            - metadata: Kategorie für Pre-Filtering
        
        Args:
            count: Anzahl der Vektoren
            normalize: Wenn True, werden Vektoren auf Länge 1 normalisiert
        
        Returns:
            Liste von Vektor-Dictionaries
        """
        if not HAS_NUMPY:
            raise ImportError(
                "NumPy wird für Vektor-Generierung benötigt. "
                "Installiere mit: pip install numpy"
            )
        
        logger.info(f"Generiere {count} Vektoren ({self.vector_dimensions}D)...")
        
        vectors = []
        
        for i in range(count):
            embedding_id = str(uuid.uuid4())
            
            # Zufälligen Vektor generieren
            vector = np.random.randn(self.vector_dimensions).astype(np.float32)
            
            # Optional: Normalisieren (wichtig für Cosine Similarity)
            if normalize:
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
            
            vectors.append({
                "embedding_id": embedding_id,
                "vector": vector.tolist(),  # Als Liste für JSON-Kompatibilität
                "metadata": {
                    "category": random.choice(self.categories),
                    "chunk_ref": f"chunk_{embedding_id}",
                }
            })
        
        return vectors
    
    def generate_query_vector(self) -> list[float]:
        """
        Generiert einen einzelnen Such-Vektor.
        
        Returns:
            Normalisierter Vektor als Liste
        """
        if not HAS_NUMPY:
            raise ImportError("NumPy wird benötigt")
        
        vector = np.random.randn(self.vector_dimensions).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()
    
    # =========================================================================
    # Relationale Daten (PostgreSQL)
    # =========================================================================
    
    def generate_users(self, count: int) -> Generator[dict, None, None]:
        """
        Generiert User-Datensätze für PostgreSQL.
        
        Args:
            count: Anzahl der User
        
        Yields:
            Dictionary mit User-Daten
        """
        logger.info(f"Generiere {count} User-Datensätze...")
        
        for i in range(count):
            user_id = str(uuid.uuid4())
            
            if self.faker:
                user = {
                    "user_id": user_id,
                    "username": self.faker.user_name(),
                    "email": self.faker.email(),
                    "full_name": self.faker.name(),
                    "created_at": self.faker.date_time_between(
                        start_date="-2y", end_date="now"
                    ),
                    "is_active": random.choice([True, True, True, False]),
                    "role": random.choice(["user", "user", "admin", "moderator"]),
                    # Feld ohne Index für Full Table Scan Tests
                    "unindexed_field": f"field_{i % 1000}",
                }
            else:
                user = {
                    "user_id": user_id,
                    "username": f"user_{i}",
                    "email": f"user_{i}@example.com",
                    "full_name": f"Test User {i}",
                    "created_at": datetime.utcnow(),
                    "is_active": True,
                    "role": "user",
                    # Feld ohne Index für Full Table Scan Tests
                    "unindexed_field": f"field_{i % 1000}",
                }
            
            yield user
    
    def generate_key_value_pairs(
        self, 
        count: int,
        value_size: int = 100
    ) -> Generator[tuple[str, str], None, None]:
        """
        Generiert Key-Value Paare für Redis.
        
        Args:
            count: Anzahl der Paare
            value_size: Größe des Values in Bytes
        
        Yields:
            Tuple (key, value)
        """
        logger.info(f"Generiere {count} Key-Value Paare...")
        
        for i in range(count):
            key = f"session:{uuid.uuid4()}"
            value = self._generate_text(value_size)
            yield (key, value)
    
    # =========================================================================
    # Hilfsmethoden
    # =========================================================================
    
    def _generate_text(self, length: int) -> str:
        """
        Generiert zufälligen Text mit der angegebenen Länge.
        
        Args:
            length: Ungefähre Länge in Zeichen
        
        Returns:
            Generierter Text
        """
        if self.faker:
            # Faker generiert realistischere Texte
            text = ""
            while len(text) < length:
                text += self.faker.paragraph(nb_sentences=3) + " "
            return text[:length]
        else:
            # Fallback: Einfache Zufallszeichen
            words = []
            current_length = 0
            while current_length < length:
                word_length = random.randint(3, 10)
                word = ''.join(random.choices(string.ascii_lowercase, k=word_length))
                words.append(word)
                current_length += word_length + 1
            return ' '.join(words)[:length]
    
    def get_random_ids(self, all_ids: list, count: int) -> list:
        """
        Wählt zufällige IDs aus einer Liste.
        
        Nützlich für Read-Tests, um zufällige Dokumente abzurufen.
        
        Args:
            all_ids: Liste aller verfügbaren IDs
            count: Anzahl der auszuwählenden IDs
        
        Returns:
            Liste zufälliger IDs
        """
        return random.sample(all_ids, min(count, len(all_ids)))
