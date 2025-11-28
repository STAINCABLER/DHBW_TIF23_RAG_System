# Planung JSON-Austausch und Backend-API

## Uebersicht Backend-API

Die Kommunikation zwischen Frontend und Backend erfolgt JSON-basiert. Dieser Entwurf beschreibt die grobe Struktur der API-Endpunkte sowie alle JSON-Objekte, die ausgetauscht werden.

Authentifizierung:

- Das Session-Token wird als HTTP-Cookie `session` vom Backend gesetzt.
- Dieses Cookie wird bei allen weiteren Requests automatisch mitgesendet und dient zur Zuordnung des Users.

### Basis-Endpunkte (Backend)

- `GET /api` – Uebersicht aller API-Endpunkte (maschinell lesbare Liste)
- `GET/POST/PUT/DELETE /api/accounts` – Verwalten von Nutzerdaten
- `POST /api/accounts/login` – Anmelden und Erzeugen eines Session-Tokens
- `POST /api/accounts/logout` – Abmelden und Deautorisieren eines Session-Tokens
- `POST /api/accounts/register` – Registrieren eines neuen Nutzers
- `GET /api/chats` – Liste der Chats eines Users (Titel und IDs)
- `GET/POST /api/chats/{id}` – Chat-Verlauf lesen und neue Fragen senden
- `GET/POST/DELETE /api/docs` – Dokumente speichern, abrufen und loeschen (PDF, Markdown, Text, CSV, JSON)

Die konkrete Auspraegung der HTTP-Methoden (GET/POST/PUT/DELETE) wird in den Detaildokumenten verfeinert.

## Frontend-Routen

Beispielhafte Zuordnung der Web-Routen:

- `GET /` – Startseite / Landing Page
- `GET /login` – Login-Seite
- `GET /register` – Registrierungsseite
- `GET /account` – Account-Ansicht / Profileinstellungen
- `GET /chat` – Aktive Chat-Ansicht
- `GET /history` – Chat-Historie

## JSON-Strukturen

Im Folgenden sind Entwurfsstrukturen fuer zentrale JSON-Objekte dargestellt. Alle Beispiele sind gueltiges JSON (Strings in Anfuehrungszeichen, Schluessel in englischer Schreibweise, Arrays statt duplizierter Keys).

### Accounts – Requests und Responses

#### Registrierung (Request)

```json
{
   "email": "user@example.com",
   "password": "secret",
   "display_name": "User"
}
```

#### Registrierung (Response)

```json
{
   "account": {
      "account_id": "abc123",
      "email": "user@example.com",
      "display_name": "User",
      "created_at": "2025-11-14T12:00:00Z"
   }
}
```

#### Login (Request)

```json
{
   "email": "user@example.com",
   "password": "secret"
}
```

#### Login (Response)

```json
{
   "account": {
      "account_id": "abc123",
      "email": "user@example.com",
      "display_name": "User"
   }
}
```

Das eigentliche Session-Token wird hierbei nicht im JSON-Body, sondern als HTTP-Cookie `session` gesetzt.

### Chat-History eines Users (Uebersicht)

```json
{
   "chats": [
      {
         "chat_id": "123456",
         "created_at": "2025-11-14T12:00:00Z"
      },
      {
         "chat_id": "789012",
         "created_at": "2025-11-14T13:00:00Z"
      }
   ]
}
```

### Einzelner Chat (Verlaufsstruktur)

```json
{
   "chat_id": "123456",
   "chat_title": "Ein Beispiel-Chat",
   "messages": [
      {
         "role": "assistant",
         "text": "Frage ...",
         "files": [
            {
               "file_id": "file-1"
            },
            {
               "file_id": "file-2"
            }
         ]
      },
      {
         "role": "user",
         "text": "Antwort / Eigene Gegenfrage...",
         "files": []
      }
   ]
}
```

### Chat – User Input (Request an Backend)

```json
{
   "chat_id": "123456",
   "question": "Frage ...",
   "files": [
      {
         "file_id": "file-1"
      },
      {
         "file_id": "file-2"
      }
   ]
}
```

Die Antwort des Backends koennte wiederum eine aktualisierte Chat-Struktur oder ein kurzes Objekt mit Antworttext und Metadaten sein.

### Chat – Antwort (Variante A, nur neue Antwort)

```json
{
   "chat_id": "123456",
   "answer_message": {
      "message_id": "msg-123",
      "role": "assistant",
      "text": "Antwort ...",
      "files": [],
      "created_at": "2025-11-14T12:00:05Z"
   },
   "updated_at": "2025-11-14T12:00:05Z"
}
```

### Chat – Paging der Nachrichten (limit/offset)

Bei `GET /api/chats/{id}` koennen optional Query-Parameter fuer Paging verwendet werden, zum Beispiel:

```text
GET /api/chats/123456?limit=50&offset=0
```

Die Antwortstruktur bleibt die oben definierte Chat-Verlaufsstruktur, jedoch mit einem auf die angefragte Fenster-Groesse begrenzten `messages`-Array.

### Dokumente – Requests und Responses ( /api/docs )

Fuer Dateien wird zwischen Metadaten (im JSON) und dem eigentlichen Dateiinhalt unterschieden. Der Inhalt kann als Multipart-Upload erfolgen; hier wird zunaechst nur die JSON-Seite der Kommunikation skizziert.

#### Dokument-Upload – Metadaten (Request)

```json
{
   "file_name": "beispiel.pdf",
   "mime_type": "application/pdf",
   "tags": [
      "rechnung",
      "2025"
   ]
}
```

#### Dokument-Metadaten (Einzelobjekt)

```json
{
   "file_id": "file-1",
   "file_name": "beispiel.pdf",
   "mime_type": "application/pdf",
   "size_bytes": 123456,
   "uploaded_at": "2025-11-14T12:00:00Z",
   "tags": [
      "rechnung",
      "2025"
   ]
}
```

#### Dokument-Upload (Response)

```json
{
   "document": {
      "file_id": "file-1",
      "file_name": "beispiel.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 123456,
      "uploaded_at": "2025-11-14T12:00:00Z",
      "tags": [
         "rechnung",
         "2025"
      ]
   }
}
```

#### Dokument-Liste (Response von GET /api/docs)

```json
{
   "documents": [
      {
         "file_id": "file-1",
         "file_name": "beispiel.pdf",
         "mime_type": "application/pdf",
         "size_bytes": 123456,
         "uploaded_at": "2025-11-14T12:00:00Z",
         "tags": [
            "rechnung",
            "2025"
         ]
      },
      {
         "file_id": "file-2",
         "file_name": "notizen.txt",
         "mime_type": "text/plain",
         "size_bytes": 7890,
         "uploaded_at": "2025-11-14T13:00:00Z",
         "tags": []
      }
   ]
}
```

Optional koennen hier zusaetzlich Paging-Informationen (`limit`, `offset`, `total`) aufgenommen werden.

#### Dokument-Delete (Request an DELETE /api/docs)

```json
{
   "file_ids": [
      "file-1",
      "file-2"
   ]
}
```

#### Dokument-Delete (Response)

```json
{
   "deleted": [
      "file-1",
      "file-2"
   ],
   "not_found": []
}
```

### API-Endpunkte als JSON-Beschreibung

Statt freiem Text kann eine maschinenlesbare Darstellung der Endpunkte verwendet werden, zum Beispiel:

```json
{
   "endpoints": [
      {
         "path": "/api/accounts",
         "method": "PUT",
         "parameters": [
            {
               "name": "account_id",
               "in": "query",
               "required": true,
               "type": "string"
            }
         ]
      },
      {
         "path": "/api/docs",
         "methods": [
            {
               "method": "GET",
               "params": [
                  {
                     "name": "file_id",
                     "in": "query",
                     "required": false,
                     "type": "string"
                  }
               ]
            }
         ]
      }
   ]
}
```

Diese Struktur laesst sich spaeter leicht erweitern (z. B. um Error-Codes, Authentifizierungsanforderungen oder Beispiel-Responses) und koennte als Basis fuer eine generierte API-Uebersicht dienen.
