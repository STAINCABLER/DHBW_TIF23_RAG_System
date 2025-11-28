# Backend API-Dokumentation (`/api/chats/<chat_id>/docs`)
Alle mit * markierten Anfragen benötigen eine aktive und gültige Session.
Andernfalls wird eine `401 - Unauthorized` zurückgegeben!

## Endpunkte
- GET [`/api/chats/<chat_id>/docs`](#get-apichatschat_iddocs)*
- GET [`/api/chats/<chat_id>/docs/<document_id>`](#get-apichatschat_iddocsdocument_id)*
- POST [`/api/chats/<chat_id>/docs`](#post-apichatschat_iddocs)*
- DELETE [`/api/chats/<chat_id>/docs/<document_id>`](#delete-apichatschat_iddocsdocument_id)*

Für alle Endpunkte unter `/api/chats` siehe [api-chats.md](./api-chats.md)


## GET `/api/chats/<chat_id>/docs`*
Gitb alle zu dem angegebenen Chat gehörenden Dateien zurück.

### Response `200 - OK`
Wird zurückgegeben, wenn dem aktuellen Nutzer der angegebene Chat gehört und dieser über eine aktive Session gehört.

Beeinhaltet nicht den Datei-Inhalt selber, sondern Daten, über welche die Datei erfragt werden kann.

```json
[
    {
        "conversation_id": 1,
        "file_id": 3,
        "file_type": "txt",
        "file_uuid": "371fd8fa-6256-4150-9c23-fb3589c3c4ac",
        "is_processed": false,
        "original_filename": "Neues Textdokument.txt",
        "uploaded_at": "2025-11-28T10:18:16.865490"
    }
]

```

### Response `401 - Unauthorized`
Wird ausgegeben, wenn der Nutzer über keine aktive Session verfügt oder nicht exisiert.

In beiden Fällen wird eine leere Antwort übergeben.


### Response `404 - Not Found`
Wird ausgegeben, wenn kein Chat mit der angegebenen Id gefunden wurde, oder wenn der aktuelle Nutzer nicht der Eigentümer dieses Chats ist.

Damit wird verhindert, dass herausgefunden werden kann, welche ChatId bereits genutzt werden bzw. kein Zugriff auf die Chats anderer möglich ist.

```
Conversation not found!
```


## GET `/api/chats/<chat_id>/docs/<document_id>`*
Gibt den Dateiinhalt des Dokumentes mit der `dokument_id` zurück.
Die Datei wird hierfür im Browser angezeigt.

### Response `200 - OK`
Wird ausgegeben, wenn die Datei zu dem aktuellen Nutzer und dem angegebenen Chat gehört.

Der Dateiinhalt wird vom Browser dargestellt.
So wird z.B. eine PDF direkt gerendert.

### Response `401 - Unauthorized`
Wird ausgegeben, wenn der Nutzer über keine aktive Session verfügt oder nicht exisiert.

In beiden Fällen wird eine leere Antwort übergeben.


### Response `404 - Not Found`
Kann in folgenden Fällen ausgebeben werden:

#### Ungültiger Chat
Wird ausgegeben, wenn kein Chat mit der angegebenen Id gefunden wurde, oder wenn der aktuelle Nutzer nicht der Eigentümer dieses Chats ist.

Damit wird verhindert, dass herausgefunden werden kann, welche ChatId bereits genutzt werden bzw. kein Zugriff auf die Chats anderer möglich ist.

```
Conversation not found!
```

#### Ungültige Datei
Wird ausgegeben, wenn keine Datei mit der angegebenen Id gefunden wurde, oder wenn diese Datei nicht zum angegeben Chat gehört.

**Hinweis**: Es findet auch eine Nutzerprüfung statt.
Diese wird aber mit einer anderen Antwort quittiert (siehe voriger Abschnitt).

Damit wird verhindert, dass herausgefunden werden kann, welche DokumentID bereits genutzt werden bzw. kein Zugriff auf die Dateien anderer möglich ist.

```
File not found!
```

## POST `/api/chats/<chat_id>/docs`*
Fügt dem angegebenen Chat ein neues Dokument hinzu.

### Request-Body
Das Dokument muss mit dem `enctype="multipart/form-data"` übertragen werden.
Des Weiteren muss das zugehörige Input-Feld den Namen `file` haben.

### Response `201 - Created`
Wird ausgegeben, wenn die Datei erfolgreich hochgeladen werden konnte

Die Datei wird ins `/upload` Verzeichnis hochgeladen - hat dort aber die `file_uuid` als Dateiname ohne Dateiendung.

Die Dateiendung wird aus dem Dateinamen gewonnen.


```json
{
    "conversation_id": 1,
    "file_id": 3,
    "file_type": "txt",
    "file_uuid": "371fd8fa-6256-4150-9c23-fb3589c3c4ac",
    "is_processed": false,
    "original_filename": "Neues Textdokument.txt",
    "uploaded_at": "2025-11-28T10:18:16.865490"
}
```

### Response ``400 - Bad Request`
In folgenden Fällen wird eine 400 zurückgebene:

#### Fehlende Datei
Wenn keine Datei mitgeschickt wird, wird folgendes zurückgegeben:

```
File required
```

#### Leeres Dateifeld
Wenn die mitgeschikcte Datei keine Daten besitzt (null)

```
Invalid file!
```

#### Leerer Dateiname
Wenn die Datei einen leeren Namen hat

```
Invalid filename
```

#### Dateiname enthält keinen `.`
Da über den Dateinamen der Dateityp gewonnen wird, ist dieser notwendig.

```
File must use . + extension!
```
#### Ungültiger Dateityp
Die Datei muss einen von folgenden Dateiendungen haben:
- .csv
- .json
- .md
- .pdf
- .txt

```
File-Type '{file_type}' not supported!
```

### Response `401 - Unauthorized`
Wird ausgegeben, wenn der Nutzer über keine aktive Session verfügt oder nicht exisiert.

In beiden Fällen wird eine leere Antwort übergeben.


### Response `404 - Not Found`
Wird ausgegeben, wenn kein Chat mit der angegebenen Id gefunden wurde, oder wenn der aktuelle Nutzer nicht der Eigentümer dieses Chats ist.

Damit wird verhindert, dass herausgefunden werden kann, welche ChatId bereits genutzt werden bzw. kein Zugriff auf die Chats anderer möglich ist.

```
Conversation not found!
```

### Response `500 - Internal Server Error`
Wird ausgegeben, wenn die Datei nicht hochgeladen werden konnte.

```
Could not upload file!
```

## DELETE `/api/chats/<chat_id>/docs/<document_id>`*
Löscht die angegebene Datei.

### Response `200 - OK`
Wird ausgegeben, wenn die Datei erfolgreich gelöscht werden konnte.

### Response `401 - Unauthorized`
Wird ausgegeben, wenn der Nutzer über keine aktive Session verfügt oder nicht exisiert.

In beiden Fällen wird eine leere Antwort übergeben.

### Response `404 - Not Found`
Kann in folgenden Fällen ausgebeben werden:

#### Ungültiger Chat
Wird ausgegeben, wenn kein Chat mit der angegebenen Id gefunden wurde, oder wenn der aktuelle Nutzer nicht der Eigentümer dieses Chats ist.

Damit wird verhindert, dass herausgefunden werden kann, welche ChatId bereits genutzt werden bzw. kein Zugriff auf die Chats anderer möglich ist.

```
Conversation not found!
```

#### Ungültige Datei
Wird ausgegeben, wenn keine Datei mit der angegebenen Id gefunden wurde, oder wenn diese Datei nicht zum angegeben Chat gehört.
Dies gilt auch dann, wenn die Datei nicht im gegebenen Ordner liegt.

**Hinweis**: Es findet auch eine Nutzerprüfung statt.
Diese wird aber mit einer anderen Antwort quittiert (siehe voriger Abschnitt).

Damit wird verhindert, dass herausgefunden werden kann, welche DokumentID bereits genutzt werden bzw. kein Zugriff auf die Dateien anderer möglich ist.

```
File not found!
```

