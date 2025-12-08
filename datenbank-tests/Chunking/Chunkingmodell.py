import re
import json
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Chunk:
    id: str
    numbering: str
    title: str
    content: str
    level: int
    section: str
    tokens: int
    full_path: str
    parent: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "numbering": self.numbering,
            "title": self.title,
            "content": self.content,
            "metadata": {
                "level": self.level,
                "section": self.section,
                "tokens": self.tokens,
                "hierarchy": {
                    "full_path": self.full_path,
                    "parent": self.parent
                }
            }
        }


class RAGChunker:
    def __init__(self):
        self.chunks: List[Chunk] = []
        self.current_section = ""

    # --- Utility: grobe Token-Schätzung (Tokens ≈ Wörter) ---

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def estimate_tokens(self, text: str) -> int:
        # kompatibel zu deinem alten Feld "tokens"
        return self.count_tokens(text)

    # --- Hierarchie-Methoden ---

    def get_level(self, numbering: str) -> int:
        if not numbering:
            return 0
        return numbering.count('.')

    def get_parent(self, numbering: str) -> Optional[str]:
        if '.' not in numbering:
            return None
        parts = numbering.split('.')
        return '.'.join(parts[:-1])

    def build_full_path(self, numbering: str) -> str:
        if '.' not in numbering:
            return numbering
        parts = numbering.split('.')
        path_elements = []
        for i in range(1, len(parts) + 1):
            path_elements.append('.'.join(parts[:i]))
        return ' > '.join(path_elements)

    # --- Stufe 1: Chunking nach Nummerierung ---

    def chunk_document(self, text: str) -> List[Chunk]:
        self.chunks = []
        lines = text.split('\n')
        numbering_pattern = r'^(\d+(?:\.\d+)*)\s+(.+)$'

        current_chunk_numbering = None
        current_chunk_title = None
        current_chunk_content = []
        chunk_counter = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = re.match(numbering_pattern, line)

            if match:
                # alten Chunk abschließen
                if current_chunk_numbering:
                    content = '\n'.join(current_chunk_content).strip()
                    if content or current_chunk_title:
                        chunk = self._create_chunk(
                            chunk_counter,
                            current_chunk_numbering,
                            current_chunk_title,
                            content
                        )
                        self.chunks.append(chunk)
                        chunk_counter += 1

                # neuen Chunk starten
                current_chunk_numbering = match.group(1)
                current_chunk_title = match.group(2).strip()
                current_chunk_content = []

                # Section-Tracking: Level 0 = neues Kapitel
                if self.get_level(current_chunk_numbering) == 0:
                    self.current_section = current_chunk_title
            else:
                if current_chunk_numbering:
                    current_chunk_content.append(line)

        # letzten Chunk abschließen
        if current_chunk_numbering:
            content = '\n'.join(current_chunk_content).strip()
            if content or current_chunk_title:
                chunk = self._create_chunk(
                    chunk_counter,
                    current_chunk_numbering,
                    current_chunk_title,
                    content
                )
                self.chunks.append(chunk)

        return self.chunks

    def _create_chunk(self, counter: int, numbering: str, title: str, content: str) -> Chunk:
        level = self.get_level(numbering)
        parent = self.get_parent(numbering)
        full_path = self.build_full_path(numbering)
        tokens = self.estimate_tokens(f"{title} {content}")
        return Chunk(
            id=f"chunk_{counter}",
            numbering=numbering,
            title=title,
            content=content,
            level=level,
            section=self.current_section,
            tokens=tokens,
            full_path=full_path,
            parent=parent
        )

    # --- Filter / Hierarchie-Abfragen ---

    def filter_by_level(self, level: int) -> List[Chunk]:
        return [chunk for chunk in self.chunks if chunk.level == level]

    def filter_by_keyword(self, keyword: str) -> List[Chunk]:
        keyword_lower = keyword.lower()
        return [
            chunk for chunk in self.chunks
            if keyword_lower in chunk.title.lower() or keyword_lower in chunk.content.lower()
        ]

    def filter_by_numbering(self, numbering: str) -> Optional[Chunk]:
        for chunk in self.chunks:
            if chunk.numbering == numbering:
                return chunk
        return None

    def get_children(self, numbering: str) -> List[Chunk]:
        return [chunk for chunk in self.chunks if chunk.parent == numbering]

    def get_all_descendants(self, numbering: str) -> List[Chunk]:
        descendants = []
        children = self.get_children(numbering)
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_all_descendants(child.numbering))
        return descendants

    def get_statistics(self) -> Dict:
        if not self.chunks:
            return {}
        total_tokens = sum(chunk.tokens for chunk in self.chunks)
        levels = {}
        for chunk in self.chunks:
            levels[chunk.level] = levels.get(chunk.level, 0) + 1
        return {
            "total_chunks": len(self.chunks),
            "total_tokens": total_tokens,
            "avg_tokens_per_chunk": total_tokens // len(self.chunks) if self.chunks else 0,
            "chunks_per_level": levels,
            "max_level": max(chunk.level for chunk in self.chunks) if self.chunks else 0
        }

    # --- Export der hierarchischen Chunks ---

    def export_to_json(self, filepath: str = None) -> str:
        chunks_dict = [chunk.to_dict() for chunk in self.chunks]
        json_str = json.dumps(chunks_dict, indent=2, ensure_ascii=False)
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
        return json_str

    def export_to_mongodb_bulk(self) -> List[Dict]:
        return [chunk.to_dict() for chunk in self.chunks]

    # --- Stufe 2: LLM-optimierte Sub-Chunks (512 Tokens + Overlap) ---

    def _split_text_into_sentences(self, text: str) -> List[str]:
        """
        Sehr einfache Satz-Splittung per Regex.
        Für echte Produktion lieber spaCy o.ä. verwenden.
        """
        # trennt nach . ! ? gefolgt von Leerzeichen/Zeilenumbruch
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def split_logical_chunk_to_llm_chunks(
        self,
        chunk: Chunk,
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        min_chunk_tokens: int = 100
    ) -> List[Dict]:
        """
        Nimmt einen hierarchischen Chunk und erzeugt Sub-Chunks
        mit max_tokens und overlap_tokens.
        Tokens ≈ Wörter.
        """
        sentences = self._split_text_into_sentences(chunk.content)
        llm_chunks: List[Dict] = []

        current_tokens = 0
        current_sentences: List[str] = []
        last_overlap_tokens: List[str] = []

        def _flush_current(sub_index: int) -> Optional[Dict]:
            nonlocal current_tokens, current_sentences, last_overlap_tokens
            if not current_sentences:
                return None
            text = " ".join(current_sentences).strip()
            token_count = self.count_tokens(text)
            if token_count < min_chunk_tokens and llm_chunks:
                # zu klein und nicht der erste: an vorherigen anhängen
                llm_chunks[-1]["chunk_text"] += " " + text
                llm_chunks[-1]["token_count"] = self.count_tokens(llm_chunks[-1]["chunk_text"])
                current_sentences = []
                current_tokens = 0
                last_overlap_tokens = []
                return None

            # Overlap für nächsten Chunk vorbereiten
            words = text.split()
            if overlap_tokens > 0 and len(words) > overlap_tokens:
                last_overlap_tokens = words[-overlap_tokens:]
            else:
                last_overlap_tokens = words

            llm_chunk = {
                "chunk_id": f"{chunk.id}_{sub_index}",
                "source_chunk_id": chunk.id,
                "numbering": chunk.numbering,
                "title": chunk.title,
                "full_path": chunk.full_path,
                "section": chunk.section,
                "level": chunk.level,
                "chunk_index": sub_index,
                "chunk_text": text,
                "token_count": token_count,
            }
            llm_chunks.append(llm_chunk)
            current_sentences = []
            current_tokens = 0
            return llm_chunk

        sub_index = 0
        for sent in sentences:
            sent_tokens = self.count_tokens(sent)
            if current_tokens + sent_tokens > max_tokens and current_sentences:
                _flush_current(sub_index)
                sub_index += 1
                # Overlap einfügen
                if overlap_tokens > 0 and last_overlap_tokens:
                    overlap_text = " ".join(last_overlap_tokens)
                    current_sentences = [overlap_text]
                    current_tokens = self.count_tokens(overlap_text)
            current_sentences.append(sent)
            current_tokens += sent_tokens

        # letzten Rest flushen
        if current_sentences:
            _flush_current(sub_index)

        return llm_chunks

    def split_into_llm_chunks(
        self,
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        min_chunk_tokens: int = 100
    ) -> List[Dict]:
        """
        Läuft über alle hierarchischen Chunks und gibt LLM-optimierte
        Sub-Chunks zurück, ready für Embeddings/DB.
        """
        all_llm_chunks: List[Dict] = []
        for chunk in self.chunks:
            subchunks = self.split_logical_chunk_to_llm_chunks(
                chunk,
                max_tokens=max_tokens,
                overlap_tokens=overlap_tokens,
                min_chunk_tokens=min_chunk_tokens
            )
            all_llm_chunks.extend(subchunks)
        return all_llm_chunks


if __name__ == "__main__":
    example_document = """
1 Einleitung
Dieses Dokument beschreibt die Architektur und Implementierung eines modernen Retrieval-Augmented-Generation (RAG) Systems für technische Dokumentation. Ziel ist es, große Mengen an heterogenen Informationen so aufzubereiten, dass sie von einem Sprachmodell effizient durchsucht und genutzt werden können, ohne dass dabei der semantische Kontext verloren geht.

1.1 Hintergrund
Klassische Suchsysteme arbeiten meist mit Schlüsselwörtern und einfachen Ranking-Algorithmen. In vielen Enterprise-Szenarien reicht dies nicht aus, da Dokumente komplex, mehrschichtig und stark vernetzt sind. RAG kombiniert semantische Vektorsuche mit einem großen Sprachmodell, um präzisere und kontextbewusste Antworten zu liefern.

1.1.1 Motivation für RAG
Unternehmen besitzen oft tausende Seiten an Protokollen, Handbüchern, E-Mails und technischen Spezifikationen. Diese Informationen sind zwar vorhanden, aber praktisch nicht zugänglich, weil klassische Volltextsuche nur Schlagwörter, nicht aber Bedeutung und Zusammenhänge versteht. RAG adressiert dieses Problem, indem es Text in Chunks zerlegt, Embeddings erzeugt und relevante Chunks dynamisch zum Prompt des Sprachmodells hinzufügt, sodass der Nutzer Antworten in natürlicher Sprache erhält, die direkt auf den vorhandenen Daten basieren.

1.2 Ziele des Systems
Das System soll eine robuste und nachvollziehbare Architektur bieten, die:
- Dokumente aus verschiedenen Quellen (PDF, Markdown, Wiki) ingestiert,
- diese in hierarchische und LLM-optimierte Chunks zerlegt,
- Embeddings für jeden Chunk berechnet,
- die Chunks in MongoDB und die Embeddings in PostgreSQL speichert
und schließlich eine API bereitstellt, über die Benutzer natürliche Fragen stellen können, ohne sich um die zugrunde liegende Datenstruktur kümmern zu müssen.

2 Technische Grundlagen
In diesem Kapitel werden die technischen Konzepte erläutert, die für das Verständnis des RAG-Systems notwendig sind, darunter Tokenisierung, Chunking-Strategien, Embeddings und Vektorsuche. Diese Grundlagen bilden die Basis für die späteren Designentscheidungen in der Implementierung.

2.1 Tokenisierung
Tokenisierung bezeichnet den Prozess, aus einem Text eine Folge von Tokens zu erzeugen, die von einem Sprachmodell verarbeitet werden kann. Je nach Modell können Tokens Wörter, Subwörter oder Zeichenfolgen sein. Für Deutsch und Englisch kommen häufig Byte-Pair-Encoding-basierte Tokenizer oder ähnliche Ansätze zum Einsatz, die lange zusammengesetzte Wörter in kleinere, modellfreundliche Einheiten zerlegen.

2.1.1 Kontextfenster und Limits
Jedes Sprachmodell hat ein begrenztes Kontextfenster, das angibt, wie viele Tokens gleichzeitig verarbeitet werden können. Wenn ein Dokument zu groß ist, um vollständig in dieses Fenster zu passen, muss es in Teilstücke zerlegt werden. Ein Chunking-Ansatz mit etwa 512 Tokens pro Chunk und 50 Tokens Overlap hat sich in vielen RAG-Szenarien als guter Kompromiss zwischen Granularität und Kontexttiefe erwiesen, da wichtige Übergänge zwischen Abschnitten durch den Overlap erhalten bleiben.

2.1.2 Bedeutung der Tokenanzahl
Die Anzahl der Tokens pro Chunk beeinflusst direkt die Antwortqualität, die Kosten für Embeddings und die Latenz bei der Anfrageverarbeitung. Zu kleine Chunks führen zu Fragmentierung und Kontextverlust, zu große Chunks können nicht mehr effizient durchsucht oder vom Modell verarbeitet werden. Daher ist eine klare Definition von Chunk-Größe, Overlap und Minimalgröße, wie in der Chunking-Strategie beschrieben, entscheidend für die Gesamtperformance des Systems.

2.2 Chunking-Strategien
Chunking-Strategien definieren, wie ein Text in kleinere Einheiten zerlegt wird. Für technische Dokumentation bietet sich eine Kombination aus strukturellem Chunking nach Überschriften und hierarchischer Nummerierung sowie einem zweiten Schritt an, in dem diese Bereiche zusätzlich nach Sätzen und Tokenanzahl aufgeteilt werden. Auf diese Weise bleiben sowohl die logische Struktur des Dokuments als auch die technischen Anforderungen des Sprachmodells berücksichtigt.

2.2.1 Hierarchisches Chunking
Beim hierarchischen Chunking werden zunächst Überschriften mit Nummerierung wie 1, 1.1, 1.1.1 erkannt und als logische Container verwendet. Jeder Container repräsentiert einen Themenblock, der wiederum Text und eventuell Unterabschnitte enthält. Diese Vorgehensweise erleichtert es, später alle Unterpunkte eines Kapitels zu finden oder die Struktur in einer Benutzeroberfläche darzustellen, ohne die eigentliche Textaufteilung für das Sprachmodell zu beeinflussen.

2.2.2 LLM-optimiertes Chunking mit Overlap
Im zweiten Schritt werden die Inhalte der hierarchischen Chunks in kleinere Sub-Chunks zerlegt, die sich am Kontextfenster des Modells orientieren. Dabei werden Sätze gesammelt, bis eine Obergrenze von zum Beispiel 512 Tokens erreicht ist. Anschließend wird ein Overlap von etwa 50 Tokens verwendet, indem die letzten Tokens des vorherigen Chunks an den Anfang des nächsten Chunks angehängt werden. Dadurch bleiben Referenzen, Einleitungen und Übergänge zwischen Abschnitten erhalten, was die Qualität der Antworten bei langen Erklärungen deutlich erhöht.

3 Implementierung im RAG-System
Dieses Kapitel beschreibt, wie die genannten Konzepte in einer konkreten Codebasis umgesetzt werden können. Die Implementierung umfasst sowohl die Extraktion der Dokumentstruktur als auch die anschließende Chunk-Erzeugung und das Speichern in den Datenbanken.

3.1 Dokument-Ingestion
Im ersten Schritt der Pipeline werden eingehende Dokumente aus verschiedenen Quellen entgegengenommen. Ein Ingestion-Service konvertiert die Dateien in reinen Text, extrahiert Metadaten wie Titel, Autor und Seitennummern und übergibt den bereinigten Text an den Chunking-Service. Fehlerhafte oder unvollständige Dokumente werden protokolliert und nicht weiter verarbeitet, um die Qualität des Indexes zu sichern.

3.2 Chunking-Service
Der Chunking-Service implementiert die zweistufige Strategie: Zuerst wird das Dokument anhand der Nummerierung und Überschriften in logische Chunks zerlegt, wie es der hierarchische Chunker tut. Anschließend werden diese logischen Chunks in LLM-optimierte Sub-Chunks mit fester Tokenanzahl und Overlap aufgeteilt. Jeder Sub-Chunk erhält eine eindeutige ID, einen Verweis auf den Ursprungschunk und Metadaten wie Nummerierung, Abschnittstitel und Pfad in der Dokumenthierarchie.

3.3 Speicherung und Embeddings
Die erzeugten Sub-Chunks werden in MongoDB als Dokumente gespeichert, während die zugehörigen Embeddings in einer separaten Tabelle in PostgreSQL abgelegt werden. Dies erlaubt eine effiziente Vektorsuche in Postgres und gleichzeitig eine flexible Speicherung der Originaltexte und Metadaten in MongoDB. Die Trennung von Textspeicherung und Vektorindex macht das System skalierbar und erleichtert spätere Anpassungen an der Embedding-Strategie, ohne die ursprünglichen Dokumente neu laden zu müssen.

3.4 Anfrageverarbeitung
Bei einer Nutzeranfrage wird der Fragetext zunächst tokenisiert und als Embedding berechnet. Anschließend wird in PostgreSQL eine Ähnlichkeitssuche gegen die Embeddings der Sub-Chunks durchgeführt, wobei die Top-k-Treffer ermittelt werden. Die zugehörigen Texte und Metadaten werden aus MongoDB gelesen und in strukturierter Form an das Sprachmodell übergeben, das daraus eine Antwort generiert, die sich direkt auf die zugrunde liegenden Dokumente stützt.
"""


    chunker = RAGChunker()
    chunks = chunker.chunk_document(example_document)

    print("Hierarchische Chunks:", len(chunks))
    for c in chunks:
        print(c.id, c.numbering, c.title)

    llm_chunks = chunker.split_into_llm_chunks(
        max_tokens=40,      # zum Testen klein halten
        overlap_tokens=10,
        min_chunk_tokens=10
    )

    print("\nLLM-Chunks:", len(llm_chunks))
    for c in llm_chunks:
        print(f"{c['chunk_id']} ({c['numbering']}): {c['token_count']} tokens")
        print(" ", c["chunk_text"])
        print()
