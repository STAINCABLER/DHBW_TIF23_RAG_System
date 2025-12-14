import requests

class PerplexityQuerier:
    """Beantwortet Fragen - Spezialist für intelligente Fragen + Synthese"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.perplexity.ai'
    
    def prompt(self, prompt: str) -> str:
        model: str = ""

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
                    'content': prompt
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

        return answer

    
    @staticmethod
    def _build_context(documents: list) -> str:
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
