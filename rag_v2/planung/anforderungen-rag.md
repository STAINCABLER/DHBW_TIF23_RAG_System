# Anforderungen an das RAG System

## Aufbau

Das RAG System soll aus folgenden Komponenten bestehen:
- 1 SQL Datenbank für Fragenkatalog
  - Enthält alle Fragen, die in Szenarien gruppiert sind
  - Jede Frage hat einen Hash um Änderungen zu erkennen
- 1 Vektorstore für Fragenkatalog
  - Enthält vektorisierte Fragen, die in Szenarien gruppiert sind
  - Beim starten des Systems werden die Fragen aus der SQL Datenbank geladen und vektorisiert, falls sie noch nicht in der Datenbank existieren, oder falls sich der hash geändert hat.
- 1 Dokumenten Datenbank für die Ingesteten Dokumente
  - Enthält Metadaten zu den Dokumenten (Dateiname, Pfad, Hash, etc.) sowie das Dokument selbst (als Cache)
  - Beim starten des Systems werden die Dokumente aus dem Ordner "ingest" geladen und in die Datenbank eingefügt, falls sie noch nicht in der datenbank existieren, oder falls sich der hash geändert hat.
- 1 Vektorstore für Wissensdatenbank (Dokumente)
  - Enthält vektorisierte Dokumente die beim starten des Systems aus der Dokumenten Datenbank geladen und vektorisiert werden, falls sie noch nicht in der Datenbank existieren, oder falls sich der hash geändert hat.
- 2 LLMs (Perplexity für Schlüsselwort-Extraktion, Gemini für Antwortgenerierung)
- Chunking und Vektorisierungskomponente für Datei-Input
- API Schnittstelle für Userinput und Antwortausgabe
- Frontend zur Interaktion mit dem User
