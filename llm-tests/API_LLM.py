#!/usr/bin/env python3
"""
RAG System - Gemini & Perplexity Backend
Konvertiert HTML/JS RAG-System zu Python-Backend mit Flask
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import PyPDF2
import google.generativeai as genai
import anthropic
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# ============================================================================
# KONFIGURATION
# ============================================================================

load_dotenv()

CONFIG = {
    'MAX_FILE_SIZE_MB': 50,
    'SUPPORTED_FORMATS': ['.pdf', '.txt', '.md', '.doc', '.docx'],
    'DEFAULT_ANALYSIS_PROMPT': 'Analysiere diesen Inhalt und gib mir eine strukturierte Zusammenfassung mit Kernpunkten.',
    'PERPLEXITY_MODELS': ['sonar', 'sonar-pro', 'sonar-reasoning'],
    'DEBUG_MODE': True,
}

# Logger Setup
logging.basicConfig(
    level=logging.DEBUG if CONFIG['DEBUG_MODE'] else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')

if not GEMINI_API_KEY or not PERPLEXITY_API_KEY:
    logger.warning('API-Keys nicht gefunden. Bitte .env Datei überprüfen.')

# ============================================================================
# DATENKLASSEN
# ============================================================================

@dataclass
class AnalysisResult:
    """Strukturiertes Analyseergebnis"""
    content: str
    timestamp: str
    source_file: str
    model: str = "gemini"
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class QueryResult:
    """Strukturiertes Abfrageergebnis"""
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
        """Extrahiert Text aus PDF-Datei"""
        try:
            text = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                logger.info(f'PDF geladen: {len(reader.pages)} Seiten')
                
                for page_num, page in enumerate(reader.pages):
                    text.append(page.extract_text())
                    logger.debug(f'Seite {page_num + 1} extrahiert')
            
            return '\n'.join(text)
        except Exception as e:
            logger.error(f'PDF-Extraktion fehlgeschlagen: {str(e)}')
            raise
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extrahiert Text aus TXT/MD-Datei"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            logger.info(f'Datei geladen: {len(content)} Zeichen')
            return content
        except Exception as e:
            logger.error(f'Datei-Extraktion fehlgeschlagen: {str(e)}')
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
            raise ValueError(f'Nicht unterstütztes Format: {file_ext}')

# ============================================================================
# GEMINI INTEGRATION
# ============================================================================

class GeminiAnalyzer:
    """Analysiert Dokumente mit Google Gemini"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        logger.info('Gemini-Analyzer initialisiert')
    
    def analyze(self, content: str, prompt: str, source_file: str = 'Unknown') -> AnalysisResult:
        """Analysiert Inhalt mit Gemini"""
        try:
            logger.info(f'Starte Gemini-Analyse für {source_file}')
            
            full_prompt = f"""
{prompt}

---
INHALT ZUM ANALYSIEREN:
---
{content[:50000]}  # Limit für API
"""
            
            response = self.model.generate_content(full_prompt)
            
            logger.info('Gemini-Analyse abgeschlossen ✓')
            
            return AnalysisResult(
                content=response.text,
                timestamp=datetime.now().isoformat(),
                source_file=source_file,
                model='gemini'
            )
        except Exception as e:
            logger.error(f'Gemini-Analyse fehlgeschlagen: {str(e)}')
            raise

# ============================================================================
# PERPLEXITY INTEGRATION
# ============================================================================

class PerplexityQuerier:
    """Stellt Fragen über Perplexity API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.perplexity.ai'
        logger.info('Perplexity-Querier initialisiert')
    
    def query(self, question: str, model: str, documents: List[AnalysisResult]) -> QueryResult:
        """Stellt Frage mit Kontext aus Dokumenten"""
        try:
            logger.info(f'Starte Perplexity-Abfrage mit Modell: {model}')
            
            # Erstelle Kontext aus Dokumenten
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
                        'content': 'Du bist ein hilfreicher Assistent, der Fragen basierend auf bereitgestellten Dokumenten beantwortet.'
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
            
            logger.info(f'Perplexity-Abfrage erfolgreich ✓ (Modell: {model})')
            
            return QueryResult(
                answer=answer,
                question=question,
                model=model,
                documents_used=len(documents),
                timestamp=datetime.now().isoformat()
            )
        except requests.exceptions.RequestException as e:
            logger.error(f'Perplexity API-Fehler: {str(e)}')
            raise
        except Exception as e:
            logger.error(f'Perplexity-Abfrage fehlgeschlagen: {str(e)}')
            raise
    
    @staticmethod
    def _build_context(documents: List[AnalysisResult]) -> str:
        """Erstellt Kontextstring aus Dokumenten"""
        if not documents:
            return ""
        
        context_parts = []
        for doc in documents:
            context_parts.append(f"[{doc.source_file}]\n{doc.content}\n")
        
        return "\n---\n".join(context_parts)
    
    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        """Erstellt finalen Prompt mit Kontext"""
        if context:
            return f"""Beantworte die folgende Frage basierend auf den bereitgestellten Dokumenten:

DOKUMENTE:
{context}

FRAGE:
{question}"""
        return question

# ============================================================================
# RAG-PIPELINE
# ============================================================================

class RAGPipeline:
    """Kombiniert Gemini-Analyse mit Perplexity-Abfragen"""
    
    def __init__(self, gemini_key: str, perplexity_key: str):
        self.analyzer = GeminiAnalyzer(gemini_key)
        self.querier = PerplexityQuerier(perplexity_key)
        self.documents: List[AnalysisResult] = []
        logger.info('RAG-Pipeline initialisiert')
    
    def analyze_document(self, file_path: str, prompt: Optional[str] = None) -> AnalysisResult:
        """Analysiert ein Dokument mit Gemini"""
        try:
            logger.info(f'--- Pipeline Schritt 1: Datei-Extraktion ---')
            content = DocumentProcessor.process_file(file_path)
            
            logger.info(f'--- Pipeline Schritt 2: Gemini-Analyse ---')
            prompt = prompt or CONFIG['DEFAULT_ANALYSIS_PROMPT']
            result = self.analyzer.analyze(content, prompt, os.path.basename(file_path))
            
            self.documents.append(result)
            logger.info(f'Dokument hinzugefügt. Gesamt: {len(self.documents)}')
            
            return result
        except Exception as e:
            logger.error(f'Dokumentanalyse fehlgeschlagen: {str(e)}')
            raise
    
    def query(self, question: str, model: str = 'sonar') -> QueryResult:
        """Stellt Frage mit Dokumentkontext"""
        if not self.documents:
            logger.warning('Keine Dokumente verfügbar')
        
        return self.querier.query(question, model, self.documents)
    
    def run_pipeline(self, file_path: str, question: str, 
                     analysis_prompt: Optional[str] = None, model: str = 'sonar') -> Dict:
        """Führt komplette RAG-Pipeline aus"""
        try:
            logger.info('=== RAG-PIPELINE GESTARTET ===')
            
            # Schritt 1: Analyse
            analysis = self.analyze_document(file_path, analysis_prompt)
            
            # Schritt 2: Abfrage
            query_result = self.query(question, model)
            
            logger.info('=== RAG-PIPELINE ERFOLGREICH ABGESCHLOSSEN ===')
            
            return {
                'status': 'success',
                'analysis': analysis.to_dict(),
                'query_result': query_result.to_dict(),
            }
        except Exception as e:
            logger.error(f'RAG-Pipeline fehlgeschlagen: {str(e)}')
            return {
                'status': 'error',
                'error': str(e),
            }

# ============================================================================
# FLASK APP
# ============================================================================

app = Flask(__name__)
CORS(app)

# State Management
rag_pipeline = None

def init_pipeline():
    """Initialisiert RAG-Pipeline"""
    global rag_pipeline
    if not GEMINI_API_KEY or not PERPLEXITY_API_KEY:
        raise RuntimeError('API-Keys nicht konfiguriert')
    rag_pipeline = RAGPipeline(GEMINI_API_KEY, PERPLEXITY_API_KEY)

@app.before_request
def check_pipeline():
    """Überprüft Pipeline-Initialisierung"""
    global rag_pipeline
    if rag_pipeline is None:
        try:
            init_pipeline()
        except RuntimeError as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health-Check Endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'documents_count': len(rag_pipeline.documents) if rag_pipeline else 0,
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analysiert hochgeladene Datei"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei hochgeladen'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Keine Datei ausgewählt'}), 400
        
        # Speichere Datei temporär
        temp_path = f'/tmp/{file.filename}'
        file.save(temp_path)
        
        prompt = request.form.get('prompt', CONFIG['DEFAULT_ANALYSIS_PROMPT'])
        result = rag_pipeline.analyze_document(temp_path, prompt)
        
        # Cleanup
        os.remove(temp_path)
        
        logger.info('✓ Datei analysiert')
        return jsonify({
            'status': 'success',
            'analysis': result.to_dict(),
            'documents_count': len(rag_pipeline.documents),
        })
    except Exception as e:
        logger.error(f'Analyse-Fehler: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query():
    """Stellt Abfrage mit Dokumentkontext"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        model = data.get('model', 'sonar')
        
        if not question:
            return jsonify({'error': 'Frage erforderlich'}), 400
        
        result = rag_pipeline.query(question, model)
        
        logger.info('✓ Abfrage beantwortet')
        return jsonify({
            'status': 'success',
            'query_result': result.to_dict(),
        })
    except Exception as e:
        logger.error(f'Query-Fehler: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/pipeline', methods=['POST'])
def pipeline():
    """Führt komplette RAG-Pipeline aus"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei hochgeladen'}), 400
        
        file = request.files['file']
        temp_path = f'/tmp/{file.filename}'
        file.save(temp_path)
        
        question = request.form.get('question', 'Analysiere den Inhalt')
        analysis_prompt = request.form.get('analysis_prompt', CONFIG['DEFAULT_ANALYSIS_PROMPT'])
        model = request.form.get('model', 'sonar')
        
        result = rag_pipeline.run_pipeline(temp_path, question, analysis_prompt, model)
        
        os.remove(temp_path)
        
        status_code = 200 if result['status'] == 'success' else 500
        logger.info(f"✓ Pipeline ausgeführt (Status: {result['status']})")
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f'Pipeline-Fehler: {str(e)}')
        return jsonify({
            'status': 'error',
            'error': str(e),
        }), 500

@app.route('/api/documents', methods=['GET'])
def documents():
    """Gibt Liste der geladenen Dokumente zurück"""
    try:
        docs = [
            {
                'source_file': doc.source_file,
                'timestamp': doc.timestamp,
                'content_length': len(doc.content),
            }
            for doc in rag_pipeline.documents
        ]
        return jsonify({
            'status': 'success',
            'documents': docs,
            'count': len(docs),
        })
    except Exception as e:
        logger.error(f'Documents-Fehler: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear():
    """Löscht alle geladenen Dokumente"""
    try:
        rag_pipeline.documents.clear()
        logger.info('✓ Alle Dokumente gelöscht')
        return jsonify({
            'status': 'success',
            'message': 'Dokumente gelöscht',
        })
    except Exception as e:
        logger.error(f'Clear-Fehler: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint nicht gefunden'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f'Server-Fehler: {str(error)}')
    return jsonify({'error': 'Interner Serverfehler'}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Test der Pipeline (optional)
    if os.getenv('TEST_MODE') == 'true':
        try:
            init_pipeline()
            logger.info('✓ Pipeline im Test-Modus initialisiert')
        except Exception as e:
            logger.error(f'Test-Initialisierung fehlgeschlagen: {str(e)}')
    
    # Starte Flask-Server
    debug_mode = CONFIG['DEBUG_MODE']
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f'=== RAG SYSTEM STARTET ===')
    logger.info(f'Debug-Modus: {debug_mode}')
    logger.info(f'Port: {port}')
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=debug_mode,
    )
