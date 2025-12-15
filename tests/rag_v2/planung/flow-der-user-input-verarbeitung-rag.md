# Flow der User-Input Verarbeitung RAG

## User-Input Verarbeitungs-Flow klein
Dieser Flow stellt die kleine Variante dess RAGs da, die für die Prüfung im Datenbanken Vorlesung gedacht ist. Da eine größere Version nicht erwünscht ist:

1. Userimput erfassen
   - Falls Datei dabei, muss diese gechunked, vektorisiert und in den Vektorstore geladen werden. (Später dann auch wieder gelöscht werden wegen DSGVO)
   - Falls kein Datei-Input, dann direkt zu Schritt 2.
2. Userimput analysieren
    - Userinput Text an LLM (Perplexity) senden um Schlüsselwörter für die Vektorsuche in der Fragenkatalog zu extrahieren.
3. Vektorsuche im Fragenkatalog
    - Extrahierte Schlüsselwörter an Vektorstore senden um relevante Fragen zu finden.
    - Hier geben sich Szenarien und ca. 10 Fragen pro Szenario zurück.
4. Vektorsuche in der Wissensdatenbank
    - Die gefundenen Fragen werden genutzt um relevante Dokumente aus der Wissensdatenbank zu suchen.
5. Kontext zusammenstellen
    - Gefundene Szenarien, Fragen und Dokumente werden zusammen mit dem Userinput in einen Kontext gepackt.
6. Antwort generieren
    - Kontext an LLM (Gemini) senden um eine Antwort zu generieren.
7. Antwort zurückgeben
    - Generierte Antwort an den User zurückgeben.

## User-Input Verarbeitungs-Flow groß

Dieser Flow stellt die große Variante des RAGs da, die wir uns für die spätere Weiterentwicklung vorstellen können:

1. User startet Chat Session
   - Neue Session ID wird generiert um den Chatverlauf zu speichern.
