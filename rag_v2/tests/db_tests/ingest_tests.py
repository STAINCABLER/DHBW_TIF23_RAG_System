"""
Ingest Performance Tests - Chunking und Vektorisierung
=======================================================

Diese Tests messen die Performance des Ingest-Prozesses:
1. Laden von Dateien verschiedener Formate (MD, TXT, JSON, PDF, CSV)
2. Chunking (Aufteilen in kleinere Textabschnitte)
3. Vektorisierung (Embedding-Generierung)

WARUM: Der Ingest-Prozess ist kritisch für die Datenqualität im RAG-System.
       Chunking-Strategien beeinflussen direkt die Retrieval-Qualität.
       (Referenz: Modul 6 - Chunking ist Datenmodellierung)

HYPOTHESE:
    - Größere Chunks sind schneller zu verarbeiten, aber weniger präzise
    - Overlap erhöht die Chunk-Anzahl, verbessert aber Kontext-Erhaltung
    - Verschiedene Dateiformate haben unterschiedliche Parsing-Kosten

Autor: RAG Performance Test Suite
"""

import time
import json
import csv
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from db_tests.base_test import BasePerformanceTest, TestContext
from utils.metrics import TestResult, ns_to_ms

logger = logging.getLogger(__name__)


# =============================================================================
# Datenklassen für Ingest
# =============================================================================

@dataclass
class Chunk:
    """Ein Text-Chunk mit Metadaten."""
    id: str
    content: str
    source_file: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list] = None


@dataclass
class IngestResult:
    """Ergebnis des Ingest-Prozesses für eine Datei."""
    source_file: str
    file_type: str
    original_length: int
    num_chunks: int
    chunks: list
    parse_time_ns: int
    chunk_time_ns: int
    vectorize_time_ns: int


# =============================================================================
# Chunking-Strategien
# =============================================================================

class ChunkingStrategy:
    """Basisklasse für Chunking-Strategien."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, text: str, source_file: str) -> list[Chunk]:
        """Teilt Text in Chunks auf."""
        raise NotImplementedError


class FixedSizeChunker(ChunkingStrategy):
    """
    Fixed-Size Chunking mit Overlap.
    
    Einfachste Strategie: Text wird in feste Größen aufgeteilt.
    Referenz: Modul 6 - "Naive Chunking"
    """
    
    def chunk(self, text: str, source_file: str) -> list[Chunk]:
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Versuche an Satzende zu brechen (innerhalb von 20% des Chunks)
            if end < len(text):
                search_start = max(end - int(self.chunk_size * 0.2), start)
                for sep in ['. ', '.\n', '\n\n', '\n']:
                    last_sep = text.rfind(sep, search_start, end)
                    if last_sep > start:
                        end = last_sep + len(sep)
                        break
            
            chunk_content = text[start:end].strip()
            
            if chunk_content:  # Leere Chunks überspringen
                chunks.append(Chunk(
                    id=f"{Path(source_file).stem}_{chunk_index}",
                    content=chunk_content,
                    source_file=source_file,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata={"strategy": "fixed_size"}
                ))
                chunk_index += 1
            
            # Nächster Start mit Overlap
            start = end - self.chunk_overlap if end < len(text) else len(text)
        
        return chunks


class SemanticChunker(ChunkingStrategy):
    """
    Semantisches Chunking basierend auf Markdown/Textstruktur.
    
    Teilt an Überschriften, Absätzen oder logischen Grenzen.
    Referenz: Modul 6 - "Semantic Chunking"
    """
    
    def chunk(self, text: str, source_file: str) -> list[Chunk]:
        chunks = []
        chunk_index = 0
        
        # Teile an Markdown-Überschriften oder Doppel-Newlines
        import re
        
        # Pattern für Markdown-Überschriften oder Absätze
        sections = re.split(r'\n(?=#{1,3}\s)|(?:\n\n)', text)
        
        current_chunk = ""
        current_start = 0
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Wenn Chunk zu groß wird, speichern und neu anfangen
            if len(current_chunk) + len(section) > self.chunk_size and current_chunk:
                chunks.append(Chunk(
                    id=f"{Path(source_file).stem}_{chunk_index}",
                    content=current_chunk.strip(),
                    source_file=source_file,
                    chunk_index=chunk_index,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                    metadata={"strategy": "semantic"}
                ))
                chunk_index += 1
                current_start += len(current_chunk)
                current_chunk = ""
            
            current_chunk += section + "\n\n"
        
        # Letzten Chunk speichern
        if current_chunk.strip():
            chunks.append(Chunk(
                id=f"{Path(source_file).stem}_{chunk_index}",
                content=current_chunk.strip(),
                source_file=source_file,
                chunk_index=chunk_index,
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                metadata={"strategy": "semantic"}
            ))
        
        return chunks


# =============================================================================
# Mock Embedding Generator
# =============================================================================

class MockEmbeddingGenerator:
    """
    Simuliert Embedding-Generierung für Performance-Tests.
    
    In einem echten System würde hier ein Modell wie:
    - sentence-transformers
    - OpenAI Ada
    - Cohere
    
    aufgerufen werden. Für Performance-Tests simulieren wir
    die typische Latenz und generieren Dummy-Vektoren.
    """
    
    def __init__(self, dimensions: int = 768, simulated_latency_ms: float = 5.0):
        """
        Args:
            dimensions: Dimension der Embedding-Vektoren
            simulated_latency_ms: Simulierte Latenz pro Embedding (ms)
        """
        self.dimensions = dimensions
        self.simulated_latency_ns = int(simulated_latency_ms * 1_000_000)
        
        try:
            import numpy as np
            self.np = np
        except ImportError:
            self.np = None
    
    def generate(self, text: str) -> list[float]:
        """Generiert ein Dummy-Embedding für den Text."""
        # Simuliere API-Latenz
        time.sleep(self.simulated_latency_ns / 1_000_000_000)
        
        if self.np:
            # Deterministisches Embedding basierend auf Text-Hash
            seed = hash(text) % (2**32)
            rng = self.np.random.RandomState(seed)
            vec = rng.randn(self.dimensions).astype('float32')
            # Normalisieren
            vec = vec / self.np.linalg.norm(vec)
            return vec.tolist()
        else:
            # Fallback ohne numpy
            import random
            random.seed(hash(text))
            vec = [random.gauss(0, 1) for _ in range(self.dimensions)]
            norm = sum(x*x for x in vec) ** 0.5
            return [x / norm for x in vec]
    
    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generiert Embeddings für mehrere Texte (Batch)."""
        return [self.generate(text) for text in texts]


# =============================================================================
# Datei-Parser
# =============================================================================

class FileParser:
    """Parser für verschiedene Dateiformate."""
    
    @staticmethod
    def parse_markdown(file_path: Path) -> str:
        """Liest Markdown-Datei."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def parse_txt(file_path: Path) -> str:
        """Liest Text-Datei."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def parse_json(file_path: Path) -> str:
        """
        Liest JSON-Datei und konvertiert zu Text.
        
        Für RAG-Systeme werden JSON-Strukturen oft in
        lesbaren Text umgewandelt.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # JSON zu lesbarem Text konvertieren
        if isinstance(data, list):
            texts = []
            for item in data:
                if isinstance(item, dict):
                    texts.append(FileParser._dict_to_text(item))
                else:
                    texts.append(str(item))
            return "\n\n".join(texts)
        elif isinstance(data, dict):
            return FileParser._dict_to_text(data)
        else:
            return str(data)
    
    @staticmethod
    def _dict_to_text(d: dict) -> str:
        """Konvertiert Dictionary zu lesbarem Text."""
        lines = []
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{key}:\n{FileParser._dict_to_text(value)}")
            elif isinstance(value, list):
                items = ", ".join(str(v) for v in value)
                lines.append(f"{key}: {items}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    @staticmethod
    def parse_csv(file_path: Path) -> str:
        """
        Liest CSV-Datei und konvertiert zu Text.
        
        Jede Zeile wird als strukturierter Absatz dargestellt.
        """
        texts = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_text = " | ".join(f"{k}: {v}" for k, v in row.items())
                texts.append(row_text)
        return "\n\n".join(texts)
    
    @staticmethod
    def parse(file_path: Path) -> str:
        """Parst Datei basierend auf Endung."""
        suffix = file_path.suffix.lower()
        
        parsers = {
            '.md': FileParser.parse_markdown,
            '.txt': FileParser.parse_txt,
            '.json': FileParser.parse_json,
            '.csv': FileParser.parse_csv,
        }
        
        parser = parsers.get(suffix)
        if parser:
            return parser(file_path)
        else:
            raise ValueError(f"Nicht unterstütztes Format: {suffix}")


# =============================================================================
# Ingest Performance Test
# =============================================================================

class IngestPerformanceTest(BasePerformanceTest):
    """
    Performance-Tests für den Ingest-Prozess.
    
    WARUM: Der Ingest-Prozess bestimmt die Qualität der RAG-Retrieval.
           Chunking-Entscheidungen beeinflussen:
           - Precision (zu kleine Chunks = fragmentierter Kontext)
           - Recall (zu große Chunks = irrelevanter Inhalt)
           - Performance (mehr Chunks = mehr Vektoren = höhere Suchkosten)
    
    HYPOTHESE:
        - Fixed-Size Chunking ist schneller als Semantic Chunking
        - Batch-Vektorisierung ist effizienter als Einzel-Aufrufe
        - Markdown-Parsing ist schneller als JSON-Parsing
    
    REFERENZ: Modul 6 (Chunking), Modul 7 (Embeddings)
    """
    
    @property
    def name(self) -> str:
        return "Ingest"
    
    @property
    def description(self) -> str:
        return """
    Ingest Performance Tests (Chunking & Vektorisierung)
    
    WARUM: Der Ingest-Prozess ist kritisch für RAG-Qualität.
           Chunking-Strategien beeinflussen Retrieval-Precision.
    
    HYPOTHESE:
        - Fixed-Size Chunking ist schneller als Semantic
        - Batch-Embedding ist effizienter als Einzel-Aufrufe
        - Verschiedene Dateiformate haben unterschiedliche Parse-Kosten
    
    REFERENZ: Modul 6 (Chunking), Modul 7 (Embeddings)
        """
    
    def setup(self) -> None:
        """Initialisiert Parser, Chunker und Embedding-Generator."""
        ingest_config = self.context.config.get("ingest", {})
        general_config = self.context.config.get("general", {})
        
        # Konfiguration laden
        self.chunk_size = ingest_config.get("chunk_size", 500)
        self.chunk_overlap = ingest_config.get("chunk_overlap", 50)
        self.vector_dimensions = general_config.get("vector_dimensions", 768)
        self.simulated_embedding_latency = ingest_config.get(
            "simulated_embedding_latency_ms", 5.0
        )
        
        # Ingest-Verzeichnis finden
        self.ingest_dir = Path(__file__).parent.parent / "ingest"
        if not self.ingest_dir.exists():
            raise FileNotFoundError(f"Ingest-Verzeichnis nicht gefunden: {self.ingest_dir}")
        
        # Dateien sammeln
        self.files = self._collect_files()
        logger.info(f"Gefunden: {len(self.files)} Dateien zum Verarbeiten")
        
        # Komponenten initialisieren
        self.parser = FileParser()
        self.fixed_chunker = FixedSizeChunker(self.chunk_size, self.chunk_overlap)
        self.semantic_chunker = SemanticChunker(self.chunk_size, self.chunk_overlap)
        self.embedding_generator = MockEmbeddingGenerator(
            dimensions=self.vector_dimensions,
            simulated_latency_ms=self.simulated_embedding_latency
        )
        
        logger.info(f"✓ Ingest-Setup abgeschlossen")
        logger.info(f"  Chunk-Größe: {self.chunk_size}, Overlap: {self.chunk_overlap}")
        logger.info(f"  Embedding-Dimensionen: {self.vector_dimensions}")
    
    def _collect_files(self) -> list[Path]:
        """Sammelt alle zu verarbeitenden Dateien."""
        files = []
        supported_extensions = {'.md', '.txt', '.json', '.csv'}
        
        for ext in supported_extensions:
            files.extend(self.ingest_dir.rglob(f"*{ext}"))
        
        return sorted(files)
    
    def teardown(self) -> None:
        """Räumt Ressourcen auf."""
        logger.info("✓ Ingest-Test abgeschlossen")
    
    def _run_tests(self) -> None:
        """Führt alle Ingest-Tests aus."""
        
        # Test 1: Datei-Parsing Performance
        self._test_file_parsing()
        
        # Test 2: Fixed-Size Chunking
        self._test_fixed_chunking()
        
        # Test 3: Semantic Chunking
        self._test_semantic_chunking()
        
        # Test 4: Chunking-Vergleich (Fixed vs. Semantic)
        self._test_chunking_comparison()
        
        # Test 5: Embedding-Generierung (Single)
        self._test_single_embedding()
        
        # Test 6: Embedding-Generierung (Batch)
        self._test_batch_embedding()
        
        # Test 7: End-to-End Ingest Pipeline
        self._test_full_pipeline()
    
    def _test_file_parsing(self) -> None:
        """Testet die Parse-Performance für verschiedene Dateiformate."""
        logger.info("Test: Datei-Parsing Performance")
        
        # Nach Dateityp gruppieren
        files_by_type = {}
        for f in self.files:
            ext = f.suffix.lower()
            if ext not in files_by_type:
                files_by_type[ext] = []
            files_by_type[ext].append(f)
        
        for ext, files in files_by_type.items():
            latencies = []
            total_chars = 0
            
            for file_path in files:
                start = time.perf_counter_ns()
                text = self.parser.parse(file_path)
                end = time.perf_counter_ns()
                
                latencies.append(end - start)
                total_chars += len(text)
            
            if latencies:
                latencies_ms = [ns_to_ms(lat) for lat in latencies]
                result = self.context.metrics_calculator.calculate(
                    test_name=f"Ingest Parse {ext.upper()}",
                    database="Ingest",
                    operation_type="parse",
                    latencies_ms=latencies_ms,
                    total_operations=len(files),
                    notes=f"Parsing von {len(files)} {ext}-Dateien ({total_chars:,} Zeichen)"
                )
                self.results.append(result)
    
    def _test_fixed_chunking(self) -> None:
        """Testet Fixed-Size Chunking."""
        logger.info("Test: Fixed-Size Chunking")
        
        latencies = []
        total_chunks = 0
        
        for file_path in self.files:
            text = self.parser.parse(file_path)
            
            start = time.perf_counter_ns()
            chunks = self.fixed_chunker.chunk(text, str(file_path))
            end = time.perf_counter_ns()
            
            latencies.append(end - start)
            total_chunks += len(chunks)
        
        latencies_ms = [ns_to_ms(lat) for lat in latencies]
        result = self.context.metrics_calculator.calculate(
            test_name="Ingest Fixed-Size Chunking",
            database="Ingest",
            operation_type="chunk",
            latencies_ms=latencies_ms,
            total_operations=len(self.files),
            notes=f"Chunking mit size={self.chunk_size}, overlap={self.chunk_overlap} → {total_chunks} Chunks"
        )
        self.results.append(result)
        
        # Speichere für späteren Vergleich
        self._fixed_chunk_count = total_chunks
    
    def _test_semantic_chunking(self) -> None:
        """Testet Semantic Chunking."""
        logger.info("Test: Semantic Chunking")
        
        latencies = []
        total_chunks = 0
        
        for file_path in self.files:
            text = self.parser.parse(file_path)
            
            start = time.perf_counter_ns()
            chunks = self.semantic_chunker.chunk(text, str(file_path))
            end = time.perf_counter_ns()
            
            latencies.append(end - start)
            total_chunks += len(chunks)
        
        latencies_ms = [ns_to_ms(lat) for lat in latencies]
        result = self.context.metrics_calculator.calculate(
            test_name="Ingest Semantic Chunking",
            database="Ingest",
            operation_type="chunk",
            latencies_ms=latencies_ms,
            total_operations=len(self.files),
            notes=f"Semantisches Chunking → {total_chunks} Chunks"
        )
        self.results.append(result)
        
        # Speichere für späteren Vergleich
        self._semantic_chunk_count = total_chunks
    
    def _test_chunking_comparison(self) -> None:
        """Vergleicht Chunking-Strategien."""
        logger.info("Test: Chunking-Strategie Vergleich")
        
        # Wähle eine repräsentative Markdown-Datei
        md_files = [f for f in self.files if f.suffix == '.md']
        if not md_files:
            logger.warning("Keine Markdown-Dateien für Vergleichstest gefunden")
            return
        
        sample_file = md_files[0]
        text = self.parser.parse(sample_file)
        
        # Fixed-Size Chunking
        fixed_start = time.perf_counter_ns()
        fixed_chunks = self.fixed_chunker.chunk(text, str(sample_file))
        fixed_end = time.perf_counter_ns()
        
        # Semantic Chunking
        semantic_start = time.perf_counter_ns()
        semantic_chunks = self.semantic_chunker.chunk(text, str(sample_file))
        semantic_end = time.perf_counter_ns()
        
        logger.info(f"  Fixed-Size: {len(fixed_chunks)} Chunks in {ns_to_ms(fixed_end - fixed_start):.2f}ms")
        logger.info(f"  Semantic: {len(semantic_chunks)} Chunks in {ns_to_ms(semantic_end - semantic_start):.2f}ms")
    
    def _test_single_embedding(self) -> None:
        """Testet Einzel-Embedding-Generierung."""
        logger.info("Test: Single Embedding Generation")
        
        # Generiere einige Chunks
        sample_texts = []
        for file_path in self.files[:3]:  # Erste 3 Dateien
            text = self.parser.parse(file_path)
            chunks = self.fixed_chunker.chunk(text, str(file_path))
            sample_texts.extend([c.content for c in chunks[:5]])  # Je 5 Chunks
        
        if not sample_texts:
            logger.warning("Keine Texte für Embedding-Test gefunden")
            return
        
        # Limitiere auf 20 für Zeitgründe (simulierte Latenz)
        sample_texts = sample_texts[:20]
        
        latencies = []
        for text in sample_texts:
            start = time.perf_counter_ns()
            _ = self.embedding_generator.generate(text)
            end = time.perf_counter_ns()
            latencies.append(end - start)
        
        latencies_ms = [ns_to_ms(lat) for lat in latencies]
        result = self.context.metrics_calculator.calculate(
            test_name="Ingest Single Embedding",
            database="Ingest",
            operation_type="vectorize",
            latencies_ms=latencies_ms,
            total_operations=len(sample_texts),
            notes=f"Einzelne Embedding-Generierung ({len(sample_texts)} Texte)"
        )
        self.results.append(result)
    
    def _test_batch_embedding(self) -> None:
        """Testet Batch-Embedding-Generierung."""
        logger.info("Test: Batch Embedding Generation")
        
        # Generiere Chunks
        sample_texts = []
        for file_path in self.files[:3]:
            text = self.parser.parse(file_path)
            chunks = self.fixed_chunker.chunk(text, str(file_path))
            sample_texts.extend([c.content for c in chunks[:5]])
        
        if not sample_texts:
            return
        
        sample_texts = sample_texts[:20]
        
        # Batch-Verarbeitung (alle auf einmal)
        start = time.perf_counter_ns()
        _ = self.embedding_generator.generate_batch(sample_texts)
        end = time.perf_counter_ns()
        
        total_time = end - start
        per_embedding = total_time / len(sample_texts)
        
        per_embedding_ms = ns_to_ms(per_embedding)
        latencies_ms = [per_embedding_ms] * len(sample_texts)
        
        result = self.context.metrics_calculator.calculate(
            test_name="Ingest Batch Embedding",
            database="Ingest",
            operation_type="vectorize",
            latencies_ms=latencies_ms,
            total_operations=len(sample_texts),
            notes=f"Batch-Embedding-Generierung ({len(sample_texts)} Texte)"
        )
        self.results.append(result)
    
    def _test_full_pipeline(self) -> None:
        """Testet die komplette Ingest-Pipeline."""
        logger.info("Test: Full Ingest Pipeline")
        
        latencies = []
        total_chunks = 0
        
        # Limitiere auf erste 5 Dateien für Zeitgründe
        test_files = self.files[:5]
        
        for file_path in test_files:
            start = time.perf_counter_ns()
            
            # 1. Parse
            text = self.parser.parse(file_path)
            
            # 2. Chunk
            chunks = self.fixed_chunker.chunk(text, str(file_path))
            
            # 3. Vectorize (nur erste 3 Chunks pro Datei für Zeitgründe)
            for chunk in chunks[:3]:
                chunk.embedding = self.embedding_generator.generate(chunk.content)
            
            end = time.perf_counter_ns()
            
            latencies.append(end - start)
            total_chunks += len(chunks)
        
        latencies_ms = [ns_to_ms(lat) for lat in latencies]
        result = self.context.metrics_calculator.calculate(
            test_name="Ingest Full Pipeline",
            database="Ingest",
            operation_type="pipeline",
            latencies_ms=latencies_ms,
            total_operations=len(test_files),
            notes=f"Parse → Chunk → Vectorize für {len(test_files)} Dateien"
        )
        self.results.append(result)
