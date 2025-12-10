#!/usr/bin/env python3
"""
RAG CLI - Interaktives Terminal-Tool mit Gemini & Perplexity
- Auto-Installation aller Dependencies
- Verschluesselte API-Keys
- Mit oder OHNE Dokument nutzbar
- Optimierte Zusammenarbeit der KIs
"""

import os
import sys
import subprocess
import json
import logging
import argparse
import tempfile
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime

# ============================================================================
# AUTO-INSTALLATION DEPENDENCIES - ZUERST AUSFÜHREN!
# ============================================================================

REQUIRED_PACKAGES = {
    'PyPDF2': 'PyPDF2>=3.0.0',
    'google.generativeai': 'google-generativeai>=0.3.0',
    'requests': 'requests>=2.31.0',
    'cryptography': 'cryptography>=41.0.0',
}

def check_and_install_dependencies():
    """Überprüft und installiert fehlende Python-Pakete"""
    print("\n" + "="*60)
    print("Überprüfe erforderliche Python-Pakete...")
    print("="*60 + "\n")
    
    missing_packages = []
    
    for package_import, package_pip in REQUIRED_PACKAGES.items():
        try:
            __import__(package_import)
            print(f"OK {package_pip.split('>=')[0]} ist installiert")
        except ImportError:
            print(f"FEHLT {package_pip.split('>=')[0]}")
            missing_packages.append((package_import, package_pip))
    
    if not missing_packages:
        print("\n[OK] Alle Pakete sind installiert!")
        print("="*60 + "\n")
        return True
    
    print(f"\n[INFO] {len(missing_packages)} Paket(e) fehlen. Installiere...")
    print("-"*60)
    
    for package_import, package_pip in missing_packages:
        try:
            print(f"[INSTALL] {package_pip}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package_pip, "--quiet"
            ])
            print(f"[OK] {package_pip} erfolgreich installiert")
        except subprocess.CalledProcessError as e:
            print(f"[FEHLER] beim Installieren von {package_pip}")
            print(f"   Details: {str(e)}")
            print(f"   Manual: pip install {package_pip}")
            return False
    
    print("\n[OK] Alle Pakete erfolgreich installiert!")
    print("="*60 + "\n")
    return True

# ============================================================================
# FÜHRE INSTALLATION VOR ALLEN ANDEREN IMPORTS AUS!
# ============================================================================

if not check_and_install_dependencies():
    print("\n[FEHLER] Abhängigkeitsinstallation fehlgeschlagen!")
    print("Bitte installiere manuell:")
    for pkg_import, pkg_pip in REQUIRED_PACKAGES.items():
        print(f"   pip install {pkg_pip}")
    sys.exit(1)

# ============================================================================
# JETZT IMPORTS NACH ERFOLGREICHER INSTALLATION
# ============================================================================

import PyPDF2
import google.generativeai as genai
import requests
from secrets_manager_auto import create_encrypted_secrets, load_secrets_interactive

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATENKLASSEN
# ============================================================================

@dataclass
class AnalysisResult:
    content: str
    timestamp: str
    source_file: str
    model: str = "gemini"

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class QueryResult:
    answer: str
    question: str
    model: str
    documents_used: int
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)

# ============================================================================
# DOKUMENTVERARBEITUNG
# ============================================================================

class DocumentProcessor:
    """Verarbeitet verschiedene Dateiformate"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Extrahiert Text aus PDF"""
        try:
            text = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                print(f"[PDF] {len(reader.pages)} Seiten gefunden")
                
                for page_num, page in enumerate(reader.pages, 1):
                    text.append(page.extract_text())
                    if page_num % 5 == 0:
                        print(f"   Seite {page_num}/{len(reader.pages)} verarbeitet")
            
            return '\n'.join(text)
        except Exception as e:
            logger.error(f"PDF-Extraktion fehlgeschlagen: {e}")
            raise
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extrahiert Text aus TXT/MD"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            print(f"[TXT] Datei geladen: {len(content)} Zeichen")
            return content
        except Exception as e:
            logger.error(f"Datei-Extraktion fehlgeschlagen: {e}")
            raise
    
    @staticmethod
    def process_file(file_path: str) -> str:
        """Verarbeitet Datei basierend auf Format"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return DocumentProcessor.extract_text_from_pdf(file_path)
        elif file_ext in ['.txt', '.md']:
            return DocumentProcessor.extract_text_from_file(file_path)
        else:
            raise ValueError(f"Format nicht unterstuetzt: {file_ext}")

# ============================================================================
# GEMINI ANALYZER (fuer Dokumentverständnis)
# ============================================================================

class GeminiAnalyzer:
    """Analysiert Dokumente - Spezialist für Dokumentverständnis"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        print("[OK] Gemini-Analyzer initialisiert")
    
    def analyze(self, content: str, source_file: str = 'Unknown') -> AnalysisResult:
        """Analysiert Dokument - strukturiert und präzise"""
        try:
            print(f"\n[GEMINI] Analysiere: {source_file}")
            
            full_prompt = f"""Analysiere dieses Dokument und erstelle eine präzise, strukturierte Zusammenfassung:

1. KERNAUSSAGEN: Die 3-5 wichtigsten Punkte
2. SCHLUESSELKONZEPTE: Zentrale Begriffe und Ideen
3. STRUKTUR: Wie ist das Dokument aufgebaut?
4. WICHTIGE DETAILS: Zahlen, Daten, spezifische Fakten

Sei präzise und factual. Halte dich an das Dokument.

---
DOKUMENT:
---
{content[:50000]}

Gib die Analyse in strukturierter Form aus."""
            
            response = self.model.generate_content(full_prompt)
            
            print("[OK] Gemini-Analyse abgeschlossen")
            
            return AnalysisResult(
                content=response.text,
                timestamp=datetime.now().isoformat(),
                source_file=source_file,
                model='gemini'
            )
        except Exception as e:
            logger.error(f"Gemini-Analyse fehlgeschlagen: {e}")
            raise

# ============================================================================
# PERPLEXITY QUERIER (für intelligente Fragen)
# ============================================================================

class PerplexityQuerier:
    """Beantwortet Fragen - Spezialist für intelligente Fragen + Synthese"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.perplexity.ai'
        print("[OK] Perplexity-Querier initialisiert")
    
    def query(self, question: str, model: str, documents: List[AnalysisResult]) -> QueryResult:
        """Beantwortet Fragen basierend auf Dokument-Kontext oder allgemein"""
        try:
            question_preview = question[:50] if len(question) > 50 else question
            print(f"\n[PERPLEXITY] Beantworte: {question_preview}...")
            
            context = self._build_context(documents)
            full_question = self._build_prompt(question, context)
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            
            payload = {
                'model': model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Du bist ein intelligenter Assistent. Antworte präzise, strukturiert und hilfreich. Nutze Recherche wenn noetig.'
                    },
                    {
                        'role': 'user',
                        'content': full_question
                    }
                ],
                'max_tokens': 2048,
                'temperature': 0.7,
            }
            
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            answer = result['choices'][0]['message']['content']
            
            print("[OK] Antwort erhalten")
            
            return QueryResult(
                answer=answer,
                question=question,
                model=model,
                documents_used=len(documents),
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Perplexity-Abfrage fehlgeschlagen: {e}")
            raise
    
    @staticmethod
    def _build_context(documents: List[AnalysisResult]) -> str:
        if not documents:
            return ""
        context_parts = []
        for doc in documents:
            context_parts.append(f"[{doc.source_file}]\n{doc.content}\n")
        return "\n---\n".join(context_parts)
    
    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        if context:
            return f"""Basierend auf folgendem Dokument, bitte diese Frage beantworten:

DOKUMENT-ANALYSE:
{context}

FRAGE:
{question}

Bitte beantworte präzise, strukturiert und hilfreich."""
        return question

# ============================================================================
# RAG PIPELINE - Interaktiv
# ============================================================================

class InteractiveRAGPipeline:
    """Interaktive RAG-Pipeline mit optimierter KI-Zusammenarbeit"""
    
    def __init__(self, gemini_key: str, perplexity_key: str):
        self.analyzer = GeminiAnalyzer(gemini_key)
        self.querier = PerplexityQuerier(perplexity_key)
        self.documents: List[AnalysisResult] = []
        self.analysis: Optional[AnalysisResult] = None
        print("[OK] RAG-Pipeline initialisiert\n")
    
    def load_and_analyze_document(self, file_path: str) -> AnalysisResult:
        """Lädt Dokument und lässt Gemini es analysieren"""
        try:
            print("\n" + "="*60)
            print("DOKUMENT LADEN & ANALYSIEREN")
            print("="*60)
            
            content = DocumentProcessor.process_file(file_path)
            
            result = self.analyzer.analyze(content, os.path.basename(file_path))
            
            self.documents.append(result)
            self.analysis = result
            
            print(f"[OK] Dokument geladen und analysiert!")
            print(f"   Gesamt Dokumente: {len(self.documents)}")
            
            return result
        except Exception as e:
            logger.error(f"Dokumentanalyse fehlgeschlagen: {e}")
            raise
    
    def interactive_questions(self, model: str = 'sonar-pro'):
        """Interaktive Terminal-Befragung"""
        print("\n" + "="*60)
        print("INTERAKTIVE BEFRAGUNG")
        print("="*60)
        print("\nStelle Fragen (exit/quit zum Beenden)\n")
        
        query_count = 0
        
        while True:
            try:
                question = input("FRAGE: ").strip()
                
                if question.lower() in ['exit', 'quit', 'q', 'e']:
                    print("\nAuf Wiedersehen!")
                    break
                
                if not question:
                    print("[INFO] Bitte gib eine Frage ein.\n")
                    continue
                
                result = self.querier.query(question, model, self.documents)
                query_count += 1
                
                print("\n" + "="*60)
                print(f"ANTWORT #{query_count}")
                print("="*60)
                print(result.answer)
                print()
            
            except KeyboardInterrupt:
                print("\n\nAuf Wiedersehen!")
                break
            except Exception as e:
                print(f"\n[FEHLER] {e}\n")
                continue
    
    def show_analysis(self):
        """Zeigt die Dokumentanalyse"""
        if not self.analysis:
            print("\n[INFO] Keine Analyse verfuegbar.")
            return
        
        print("\n" + "="*60)
        print("DOKUMENTANALYSE")
        print("="*60)
        print(f"Datei: {self.analysis.source_file}")
        print(f"Modell: {self.analysis.model.upper()}")
        print("-"*60)
        print(self.analysis.content)

# ============================================================================
# CLI MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="RAG CLI - Interaktives Gemini & Perplexity Terminal Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Verwendung:
  python rag_cli_interactive.py --setup-secrets        # API-Keys speichern
  python rag_cli_interactive.py --file dokument.pdf    # Mit Datei
  python rag_cli_interactive.py                         # Ohne Datei
        """
    )
    
    parser.add_argument('--setup-secrets', action='store_true', help='API-Keys verschluesselt speichern')
    parser.add_argument('--file', type=str, help='Dokument laden (optional)')
    parser.add_argument('--model', type=str, default='sonar-pro', help='Perplexity Model (default: sonar-pro)')
    
    args = parser.parse_args()
    
    # Setup Secrets
    if args.setup_secrets:
        print("\n" + "="*60)
        print("SETUP: API-Keys verschluesselt speichern")
        print("="*60)
        create_encrypted_secrets()
        return
    
    # Lade Secrets
    print("\n" + "="*60)
    print("Lade API-Keys...")
    print("="*60)
    
    try:
        gemini_key, perplexity_key = load_secrets_interactive()
        print("[OK] API-Keys erfolgreich geladen\n")
    except Exception as e:
        print(f"\n[FEHLER] {e}")
        print("Bitte erst Setup durchfuehren: python rag_cli_interactive.py --setup-secrets")
        sys.exit(1)
    
    # Initialisiere Pipeline
    pipeline = InteractiveRAGPipeline(gemini_key, perplexity_key)
    
    # Hauptlogik
    if args.file:
        # Mit Datei
        if not os.path.exists(args.file):
            print(f"\n[FEHLER] Datei nicht gefunden: {args.file}")
            sys.exit(1)
        
        try:
            analysis = pipeline.load_and_analyze_document(args.file)
            pipeline.show_analysis()
            pipeline.interactive_questions(args.model)
        
        except Exception as e:
            print(f"\n[FEHLER] {e}")
            sys.exit(1)
    else:
        # OHNE Datei - direkte Fragen an Perplexity
        print("\n" + "="*60)
        print("INTERAKTIVE BEFRAGUNG (OHNE DOKUMENT)")
        print("="*60)
        print("\nStelle Fragen direkt an Perplexity!")
        print("(exit/quit zum Beenden)\n")
        
        query_count = 0
        
        while True:
            try:
                question = input("FRAGE: ").strip()
                
                if question.lower() in ['exit', 'quit', 'q', 'e']:
                    print("\nAuf Wiedersehen!")
                    break
                
                if not question:
                    print("[INFO] Bitte gib eine Frage ein.\n")
                    continue
                
                result = pipeline.querier.query(question, args.model, [])
                query_count += 1
                
                print("\n" + "="*60)
                print(f"ANTWORT #{query_count}")
                print("="*60)
                print(result.answer)
                print()
            
            except KeyboardInterrupt:
                print("\n\nAuf Wiedersehen!")
                break
            except Exception as e:
                print(f"\n[FEHLER] {e}\n")
                continue

if __name__ == '__main__':
    main()
