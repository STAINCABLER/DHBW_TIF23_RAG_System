Beispiel: Eine Seite Betriebsanleitung ("Wasserfilter wechseln")

1. Chunk-Grenze
Chunk = Abschnitt der Betriebsanleitung
Begründung: Jeder Abschnitt beschreibt eine abgeschlossene Funktion (z. B. „Vorbereitung“, „Filter entnehmen“, „Neuen Filter einsetzen“). Das entspricht dem Access-Pfad: „Finde den relevanten funktionalen Schritt“.

2. Chunk-Größe
150–250 Wörter pro Chunk
Begründung:

genug Information für LLM-Kontext

nicht zu groß → schnelle Punktabfrage

nicht zu klein → keine Fragmentierung der funktionalen Schritte

3. Overlap
0–10% (nur bei Absatzbruch)
Begründung: Der Text ist funktional gegliedert. Leichte Überlappung verhindert harte Schnitte, wenn wichtige Informationen genau zwischen zwei Absätzen stehen.

4. Metadaten (precompute)
Pflicht:

doc_id

chunk_id

section_title

position

product_family

version

keywords

Optional:

estimated_time

tools_required

safety_level

Begründung:
Metadaten werden für Retrieval-Filter benötigt (z. B. „Filterwechsel“, „Modell KA-22“, „Sicherheitsstufe niedrig“).

5. JSON-Beispiel eines Chunks
{
  "doc_id": "manual_ka22_2024",
  "chunk_id": "manual_ka22_2024_03",
  "position": 3,
  "section_title": "Filter entnehmen",
  "text": "Um den Wasserfilter zu entnehmen, öffnen Sie zunächst die Frontabdeckung ...",
  "keywords": ["filter", "wasserfilter", "entnehmen", "wartung"],
  "product_family": "KA-22",
  "version": "2024",
  "estimated_time": "2 min",
  "tools_required": ["keine"],
  "safety_level": "low",
  "embedding_ref": "emb_ka22_03"
}
6. Kurzbegründung (3 Sätze)
„Chunking folgt dem funktionsorientierten Access-Pfad: Jede Chunks ist ein abgeschlossener Schritt der Anleitung. Die Größe von ~200 Wörtern vermeidet Fragmentierung und sorgt für schnelle Punktabfragen. Precomputed Metadaten ermöglichen gezieltes Retrieval (z. B. nach Produktfamilie, Abschnitt oder Sicherheitsstufe).“

