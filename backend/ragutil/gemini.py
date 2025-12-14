import google.generativeai

class GeminiAnalyzer:
    """Analysiert Dokumente - Spezialist für Dokumentverständnis"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        google.generativeai.configure(api_key=api_key)
        self.model = google.generativeai.GenerativeModel('gemini-pro')
        print("[OK] Gemini-Analyzer initialisiert")
    
    def process_prompt(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text,
