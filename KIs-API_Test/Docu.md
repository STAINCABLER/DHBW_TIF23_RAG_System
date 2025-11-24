# Gemini + Perplexity RAG System - Dokumentation

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Systemarchitektur](#systemarchitektur)
3. [Installation und Setup](#installation-und-setup)
4. [API-Konfiguration](#api-konfiguration)
5. [Funktionsweise](#funktionsweise)
6. [Wichtige Hinweise](#wichtige-hinweise)
7. [Fehlerbehebung](#fehlerbehebung)
8. [Best Practices](#best-practices)
9. [Erweiterungsmöglichkeiten](#erweiterungsmöglichkeiten)

---

## Überblick

Dieses RAG (Retrieval-Augmented Generation) System kombiniert **Google Gemini** für multimodale Dokumentanalyse mit **Perplexity AI** für intelligente Frage-Antwort-Funktionalität. Das System ermöglicht:

- **Automatische Dokumentanalyse** durch Gemini (Bilder, PDFs)
- **Persistente Speicherung** aller Analysen
- **Kontextbewusste Antworten** durch Perplexity mit Zugriff auf alle gespeicherten Dokumente
- **Benutzerfreundliche Web-Oberfläche**

### Kernfunktionen

- ✅ Datei-Upload (Bilder: JPG, PNG, GIF, PDF-Dokumente)
- ✅ Automatische Analyse nach Upload
- ✅ Speicherung aller Analyseergebnisse
- ✅ Fragen zu hochgeladenen Dokumenten oder allgemeine Fragen
- ✅ Perplexity nutzt alle gespeicherten Dokumente als Context

---

## Systemarchitektur

### Workflow-Diagramm

┌─────────────────┐
│ User lädt Datei │
│     hoch        │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ 1. Gemini API       │
│    analysiert       │
│    automatisch      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ 2. Analyse wird     │
│    lokal im Array   │
│    gespeichert      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ User stellt Frage   │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ 3. Perplexity API   │
│    nutzt alle       │
│    Analysen als     │
│    Context          │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ 4. Antwort wird     │
│    angezeigt        │
└─────────────────────┘

### Komponenten

| Komponente | Technologie | Zweck |
|------------|-------------|-------|
| **Frontend** | HTML5 + Vanilla JavaScript | Benutzeroberfläche |
| **Dokumentanalyse** | Google Gemini 1.5 Pro | Bild- und Dokumentverarbeitung |
| **Q&A Engine** | Perplexity Sonar Pro | Intelligente Antwortgenerierung |
| **Speicherung** | JavaScript Array (in-memory) | Temporäre Dokumentspeicherung |

---

## Installation und Setup

### Voraussetzungen

- Moderner Webbrowser (Chrome, Firefox, Safari, Edge)
- Aktive Internetverbindung
- Gültige API-Keys für:
  - Google Gemini API
  - Perplexity API

### Schritt 1: Datei vorbereiten

1. Speichere die HTML-Datei lokal (z.B. `gemini-perplexity-rag.html`)
2. Öffne die Datei in einem Texteditor (VS Code, Sublime, Notepad++)

### Schritt 2: Datei verwenden

Öffne die HTML-Datei direkt im Browser:
- **Windows**: Doppelklick auf die Datei
- **macOS**: Rechtsklick → "Öffnen mit" → Browser wählen
- **Linux**: `firefox gemini-perplexity-rag.html` oder `chromium gemini-perplexity-rag.html`

---

## API-Konfiguration

### ⚠️ KRITISCH: API Keys eintragen

**Zeile 260-261 im HTML-Code:**

// API Keys (stored in code)
const GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY_HERE';
const PERPLEXITY_API_KEY = 'YOUR_PERPLEXITY_API_KEY_HERE';

**Ersetze die Platzhalter mit deinen echten API Keys!**

### Gemini API Key erhalten

1. Gehe zu [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Klicke auf "Get API Key"
3. Erstelle ein neues Projekt oder wähle ein bestehendes
4. Kopiere den API Key

**Format:** `AIzaSy...` (39 Zeichen)

### Perplexity API Key erhalten

1. Gehe zu [Perplexity Settings](https://www.perplexity.ai/settings/api)
2. Erstelle einen neuen API Key
3. Kopiere den Key

**Format:** `pplx-...` (beginnt mit "pplx-")

**Kosten:**
- Gemini: Generöser Free Tier (15 Anfragen/Minute)
- Perplexity: $5/Monat mit Pro-Account oder Pay-per-use

### Beispiel-Konfiguration

const GEMINI_API_KEY = 'AIzaSyBX7H3k9pL2mN5qR8tU1vW4xY6zA2bC3dE';
const PERPLEXITY_API_KEY = 'pplx-1a2b3c4d5e6f7g8h9i0j';

---

## Funktionsweise

### 1. Datei-Upload und automatische Analyse

**Was passiert:**

1. User wählt eine Datei (Bild oder PDF)
2. **Automatisch** wird `analyzeBtn.click()` getriggert
3. Gemini analysiert das Dokument:
   - Extrahiert Text
   - Erkennt Objekte/Themen
   - Generiert Zusammenfassung
   - Identifiziert Key Insights
   - Kategorisiert Inhalt
4. Analyse wird im `storedDocuments` Array gespeichert

**Code-Referenz:**

fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) {
        setTimeout(() => analyzeBtn.click(), 500);
    }
});

### 2. Daten-Speicherung

**Struktur eines gespeicherten Dokuments:**

{
    id: 1,
    file_id: "file_1732456789012",
    file_name: "diagram.png",
    stored_at: "2025-11-24T13:26:29.012Z",
    analysis: {
        summary: "...",
        key_insights: [...],
        text_content: "...",
        categories: [...],
        sentiment: "informativ",
        metadata: { ... }
    }
}

**Wichtig:** Daten werden **nur im Browser-RAM** gespeichert (nicht persistent). Bei Seitenneuladung gehen Daten verloren.

### 3. Perplexity-Abfrage mit Context

**Was passiert:**

1. User stellt eine Frage
2. System sammelt **alle** gespeicherten Analysen
3. Erstellt Context-String aus allen Dokumenten:

context = storedDocuments.map(doc => `
    Dokument: ${doc.file_name}
    Zusammenfassung: ${doc.analysis.summary}
    Erkenntnisse: ${doc.analysis.key_insights.join('; ')}
    Kategorien: ${doc.analysis.categories.join(', ')}
    Text-Inhalt: ${doc.analysis.text_content}
`).join('\n\n---\n\n');

4. Perplexity erhält Query + vollständigen Context
5. Antwort wird generiert mit Zugriff auf alle Dokument-Informationen

**Code-Referenz:**

const perplexityResult = await queryPerplexity(
    query, 
    context,  // Alle Dokumente!
    PERPLEXITY_API_KEY, 
    model
);

### 4. Modell-Auswahl

**Verfügbare Perplexity-Modelle:**

| Modell | Beschreibung | Use Case |
|--------|--------------|----------|
| `sonar-pro` | Standard (empfohlen) | Allgemeine Fragen, gute Balance |
| `sonar-reasoning` | Komplexe Analysen | Mehrstufiges Reasoning, technische Fragen |
| `sonar` | Schnell | Einfache Fragen, schnelle Antworten |

---

## Wichtige Hinweise

### 🔴 Kritische Punkte

#### 1. API Keys im Code

**Problem:** API Keys sind im Frontend-Code sichtbar

**Risiken:**
- Jeder mit Browser DevTools kann die Keys sehen
- Keys können gestohlen und missbraucht werden
- Unerwartete API-Kosten

**Lösungen für Produktion:**

// ❌ NICHT SO (im Frontend):
const GEMINI_API_KEY = 'AIzaSy...';

// ✅ SO (mit Backend):
const response = await fetch('/api/analyze', {
    method: 'POST',
    body: formData
});
// Backend verwaltet API Keys sicher

**Empfehlung:**
- Für **persönliche Nutzung/Testing**: OK
- Für **öffentliche Deployment**: Backend mit API Key Management nötig

#### 2. In-Memory Storage

**Problem:** Daten gehen bei Seitenneuladen verloren

**Aktuelle Implementierung:**
let storedDocuments = []; // RAM only

**Für Persistenz:**

// localStorage (einfach, clientseitig):
function storeAnalysis(fileId, fileName, analysisData) {
    const document = { id: Date.now(), file_id: fileId, ... };
    let docs = JSON.parse(localStorage.getItem('documents') || '[]');
    docs.push(document);
    localStorage.setItem('documents', JSON.stringify(docs));
}

// Beim Laden:
storedDocuments = JSON.parse(localStorage.getItem('documents') || '[]');

**Alternativ:** Backend-Datenbank (PostgreSQL, MongoDB, siehe vorherige Dokumentation)

#### 3. Simulations-Code

**Wichtig:** Das System verwendet **Simulations-Code** für API-Calls!

**Was funktioniert:**
- ✅ UI/UX Flow
- ✅ Datei-Upload
- ✅ State Management
- ✅ Context-Aggregation

**Was simuliert ist:**
- ⚠️ Gemini API Calls
- ⚠️ Perplexity API Calls

**Für echte API-Integration:**

Ersetze in `analyzeWithGemini()` (ca. Zeile 315):

// Aktuell: Simulation
return new Promise((resolve) => {
    setTimeout(() => resolve({ summary: "..." }), 2000);
});

// Ersetzen mit echtem API Call:
const formData = new FormData();
formData.append('file', file);

const response = await fetch(
    'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent',
    {
        method: 'POST',
        headers: { 'x-goog-api-key': apiKey },
        body: JSON.stringify({
            contents: [{
                parts: [
                    { text: prompt },
                    { 
                        inline_data: {
                            mime_type: file.type,
                            data: await fileToBase64(file)
                        }
                    }
                ]
            }]
        })
    }
);
const data = await response.json();
return parseGeminiResponse(data);

Ersetze in `queryPerplexity()` (ca. Zeile 357):

// Aktuell: Simulation
return new Promise((resolve) => {
    setTimeout(() => resolve({ answer: "..." }), 2500);
});

// Ersetzen mit echtem API Call:
const response = await fetch('https://api.perplexity.ai/chat/completions', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        model: model,
        messages: [
            {
                role: 'system',
                content: `Du bist ein hilfreicher Assistent. Nutze folgenden Context:\n\n${context}`
            },
            {
                role: 'user',
                content: query
            }
        ]
    })
});
const data = await response.json();
return {
    answer: data.choices[0].message.content,
    model: model,
    tokens_used: data.usage.total_tokens
};

#### 4. File Size Limits

**Browser-Limits:**
- Max. 100-500 MB pro Datei (abhängig vom Browser)
- Große Dateien können Browser zum Einfrieren bringen

**API-Limits:**
- Gemini: Max. 20 MB Bilder, 10 MB PDFs
- Perplexity: Context-Limit ~100k Tokens

**Empfehlung:**
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    const maxSizeMB = 10;
    
    if (file.size > maxSizeMB * 1024 * 1024) {
        alert(`Datei zu groß! Max. ${maxSizeMB}MB erlaubt.`);
        fileInput.value = '';
        return;
    }
});

---

## Fehlerbehebung

### Problem: "API Key ungültig"

**Symptome:**
- Fehler in Browser Console: `401 Unauthorized`
- Status-Meldung: "Fehler bei der Analyse"

**Lösungen:**
1. Überprüfe API Keys in Zeile 260-261
2. Stelle sicher, dass keine Leerzeichen vor/nach dem Key sind
3. Gemini Key muss mit `AIza` beginnen
4. Perplexity Key muss mit `pplx-` beginnen
5. Teste Keys direkt in der API-Dokumentation

### Problem: "CORS Error"

**Symptome:**
- Console Error: `Access-Control-Allow-Origin`
- Requests werden blockiert

**Ursache:** Browser blockiert API-Calls von lokalen Files

**Lösungen:**

**Option 1: Python HTTP Server**
# Im Verzeichnis der HTML-Datei:
python3 -m http.server 8000
# Öffne: http://localhost:8000/gemini-perplexity-rag.html

**Option 2: Node.js HTTP Server**
npx http-server -p 8000
# Öffne: http://localhost:8000/gemini-perplexity-rag.html

**Option 3: VS Code Live Server Extension**
- Installiere "Live Server" Extension
- Rechtsklick auf HTML → "Open with Live Server"

### Problem: Datei wird nicht hochgeladen

**Checkliste:**
- ✓ Dateiformat unterstützt? (JPG, PNG, GIF, PDF)
- ✓ Dateigröße < 10 MB?
- ✓ Browser-Berechtigung für Datei-Zugriff?
- ✓ JavaScript aktiviert?

### Problem: Perplexity antwortet ohne Context

**Ursache:** Keine Dokumente gespeichert oder Context-Generierung fehlerhaft

**Debug:**
// In Browser Console:
console.log(storedDocuments);
// Sollte Array mit Dokumenten zeigen

**Fix:** Stelle sicher, dass Gemini-Analyse erfolgreich war vor Perplexity-Query

---

## Best Practices

### 1. Sicherheit

// ✅ DO: API Keys aus Environment Variables (bei Backend)
const apiKey = process.env.GEMINI_API_KEY;

// ❌ DON'T: Hardcoded Keys in öffentlichem Code
const apiKey = 'AIzaSyBX7H3k9pL2mN5qR8tU1vW4xY6zA2bC3dE';

// ✅ DO: Rate Limiting
let requestCount = 0;
const MAX_REQUESTS_PER_MINUTE = 15;

// ✅ DO: Input Validation
if (file.size > 10 * 1024 * 1024) {
    throw new Error('File too large');
}

### 2. Performance

// ✅ DO: Caching für wiederholte Fragen
const cache = new Map();
if (cache.has(query)) {
    return cache.get(query);
}

// ✅ DO: Lazy Loading für große Dokumente
const chunks = splitIntoChunks(largeDocument, 1000);

// ✅ DO: Debouncing für User Input
let debounceTimer;
userQuery.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        // Validate input
    }, 500);
});

### 3. User Experience

// ✅ DO: Progress Indicators
showStatus('Gemini analysiert... 0%');
// Update progress
showStatus('Gemini analysiert... 50%');

// ✅ DO: Error Messages mit Kontext
catch (error) {
    if (error.status === 401) {
        showStatus('API Key ungültig. Bitte überprüfen.', 'error');
    } else if (error.status === 429) {
        showStatus('Rate Limit erreicht. Bitte warten.', 'error');
    }
}

// ✅ DO: Keyboard Shortcuts
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        queryBtn.click();
    }
});

### 4. Testing

// Test verschiedene Dateitypen
const testFiles = [
    'test.jpg',   // Foto
    'test.png',   // Diagramm
    'test.pdf'    // Dokument
];

// Test verschiedene Query-Typen
const testQueries = [
    'Was zeigt das Bild?',                    // Spezifisch
    'Zusammenfassung aller Dokumente',        // Übergreifend
    'Aktuelle Nachrichten zu KI'              // Ohne Context
];

---

## Erweiterungsmöglichkeiten

### 1. Persistente Speicherung

**LocalStorage-Integration:**

// Speichern
function saveToLocalStorage() {
    localStorage.setItem('rag_documents', JSON.stringify(storedDocuments));
}

// Laden
function loadFromLocalStorage() {
    const saved = localStorage.getItem('rag_documents');
    if (saved) {
        storedDocuments = JSON.parse(saved);
    }
}

// Bei jedem Update
storeAnalysis(...);
saveToLocalStorage();

**IndexedDB für große Datenmengen:**

const dbRequest = indexedDB.open('RAG_Database', 1);

dbRequest.onsuccess = (event) => {
    const db = event.target.result;
    const transaction = db.transaction(['documents'], 'readwrite');
    const store = transaction.objectStore('documents');
    store.add(document);
};

### 2. Backend-Integration

**Express.js Backend-Beispiel:**

// server.js
const express = require('express');
const app = express();

app.post('/api/analyze', async (req, res) => {
    const apiKey = process.env.GEMINI_API_KEY;
    const result = await callGeminiAPI(req.file, apiKey);
    res.json(result);
});

app.post('/api/query', async (req, res) => {
    const apiKey = process.env.PERPLEXITY_API_KEY;
    const result = await callPerplexityAPI(req.body.query, apiKey);
    res.json(result);
});

app.listen(3000);

**Frontend anpassen:**

async function analyzeWithGemini(file, prompt) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('prompt', prompt);
    
    const response = await fetch('http://localhost:3000/api/analyze', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

### 3. Erweiterte Features

**Batch-Upload:**

<input type="file" multiple id="file-input">

fileInput.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files);
    
    for (const file of files) {
        await analyzeWithGemini(file, prompt);
    }
});

**Export-Funktion:**

function exportAnalyses() {
    const dataStr = JSON.stringify(storedDocuments, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'rag_analyses.json';
    a.click();
}

**Suchfunktion:**

function searchDocuments(searchTerm) {
    return storedDocuments.filter(doc => 
        doc.analysis.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.analysis.key_insights.some(insight => 
            insight.toLowerCase().includes(searchTerm.toLowerCase())
        )
    );
}

**Chat-Historie:**

const chatHistory = [];

function addToHistory(query, answer) {
    chatHistory.push({
        timestamp: new Date().toISOString(),
        query: query,
        answer: answer,
        context_docs: storedDocuments.length
    });
}

function displayHistory() {
    // Zeige alle bisherigen Fragen und Antworten
}

### 4. Visualisierungen

**Chart.js Integration:**

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

function visualizeCategories() {
    const categories = {};
    storedDocuments.forEach(doc => {
        doc.analysis.categories.forEach(cat => {
            categories[cat] = (categories[cat] || 0) + 1;
        });
    });
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(categories),
            datasets: [{
                label: 'Dokumente pro Kategorie',
                data: Object.values(categories)
            }]
        }
    });
}

---

## Zusammenfassung

### Schnellstart-Checklist

- [ ] HTML-Datei heruntergeladen
- [ ] API Keys eingetragen (Zeile 260-261)
- [ ] Datei im Browser geöffnet
- [ ] Test-Datei hochgeladen
- [ ] Automatische Analyse funktioniert
- [ ] Testfrage gestellt
- [ ] Perplexity antwortet mit Context

### Typische Workflows

**Workflow 1: Dokument analysieren**
1. Datei hochladen → Automatische Analyse
2. Ergebnis ansehen
3. Weitere Dokumente hochladen

**Workflow 2: Fragen zu Dokumenten**
1. Mehrere Dateien hochladen
2. Frage zu einem spezifischen Dokument stellen
3. Frage zu allen Dokumenten stellen

**Workflow 3: Allgemeine Fragen**
1. Keine Datei hochladen
2. Direkt Frage stellen (z.B. "Was ist Redis?")
3. Perplexity antwortet ohne Dokument-Context

### Support und Weiterentwicklung

**Bei Problemen:**
1. Browser Console öffnen (F12) → Fehler prüfen
2. API Keys validieren
3. Datei-Format und -Größe prüfen
4. Falls nötig: Lokalen Server starten

**Für Produktiv-Deployment:**
1. Backend mit API Key Management implementieren
2. Datenbank für persistente Speicherung einrichten
3. Rate Limiting und Caching implementieren
4. Error Handling verbessern
5. Security Audit durchführen

---

**Version:** 1.0  
**Datum:** 24. November 2025  
**Autor:** RAG System Development Team