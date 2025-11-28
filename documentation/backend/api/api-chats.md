# Backend API-Dokumentation (`/api/chats`)
Alle mit * markierten Anfragen benötigen eine aktive und gültige Session.
Andernfalls wird eine `401 - Unauthorized` zurückgegeben!

## Endpunkte
- GET [`/api/chats`](#get-apichats)*
- POST [`/api/chats`](#post-apichats)*
- GET [`/api/chats/<chat_id>`](#get-apichatschat_id)*
- POST [`/api/chats/<chat_id>`](#post-apichatschat_id)*

Für alle Endpunkte unter `/api/chats/<chat_id>/docs` siehe [api-docs.md](./api-docs.md)


## GET `/api/chats`*
Gitb alle zu dem angemeldeten Nutzer gehörenden Chats aus.
Dies beeinhaltet nicht die einzelnen Chatnachrichten.


### Response `200 - OK`
Wird ausgegeben, wenn der zur Session gehörende Nutzer existiert.

```json
[
    {
        "conversation_id": 1,
        "created_at": "2025-11-28T08:57:59.192508",
        "is_active": true,
        "title": "Neuer Chat",
        "updated_at": "2025-11-28T08:57:59.192508",
        "user_id": 1
    },
    {
        "conversation_id": 2,
        "created_at": "2025-11-29T05:25:54.138715",
        "is_active": true,
        "title": "Neuer Chat 2",
        "updated_at": "2025-11-29T05:28:25.895642",
        "user_id": 1
    }
]
```

### Response `401 - Unauthorized`
Wird ausgegeben, wenn der Nutzer über keine aktive Session verfügt oder nicht exisiert.

In beiden Fällen wird eine leere Antwort übergeben.

## POST `/api/chats`*
Erstellt unter dem aktuellen Nutzer einen neuen Chat

### Request-Body
```json
{
    "title": "Chat Titel"
}
```
- `title` *(optional)*: Der Titel des neuen Chats. Default: `New Chat`



### Response `201 - Created`
Wird zurückgeben, wenn der neue Chat erfoglreich erstellt werden konnte.
Hierbei wird auch der neue Chat mitgeschickt.

```json
{
    "conversation_id": 1,
    "created_at": "2025-11-28T08:57:59.192508",
    "is_active": true,
    "title": "Neuer Chat",
    "updated_at": "2025-11-28T08:57:59.192508",
    "user_id": 1
}
```
### Response `400 - Bad Request`
Wird ausgegeben, wenn kein `user_input` im Request-Body vorliegt.

```
Request requires user_input!
```

### Response `401 - Unauthorized`
Wird ausgegeben, wenn der Nutzer über keine aktive Session verfügt oder nicht exisiert.

In beiden Fällen wird eine leere Antwort übergeben.

## GET `/api/chats/<chat_id>`*
Gibt den angebeben Chat mit der `chat_id` zurück.
Dieser beeinhaltet auch alle Chat-Nachrichten.

### Response `200 - OK`
Wird ausgegeben, wenn der angebene Chat existiert und auch zu dem angemeldeten Nutzer gehört.
```json
{
    "conversation_id": 1,
    "created_at": "2025-11-28T08:57:59.192508",
    "is_active": true,
    "messages": [
        {
            "content": "Hallo Welt",
            "conversation_id": 1,
            "message_id": 3,
            "metadata": {},
            "role": "user",
            "timestamp": "2025-11-28T09:17:00.293775"
        },
        {
            "content": "Platzhalter",
            "conversation_id": 1,
            "message_id": 4,
            "metadata": {},
            "role": "assistant",
            "timestamp": "2025-11-28T09:17:00.370961"
        }
    ],
    "title": "Neuer Chat",
    "updated_at": "2025-11-28T08:57:59.192508",
    "user_id": 1
}
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

## POST `/api/chats/<chat_id>`*
Fügt dem angegebenen Chat eine neue Nachricht hinzu.
Zurück gegeben wird die durch das RAG-Verarbeitete Anfrage

### Request-Body
```json
{
    "user_input": "Nutzereingabe hier einfügen"
}
```
- `user_input`: Eingabe des Nutzers, welche vom RAG verarbeitet werden soll

### Response `201 - Created`
Wird ausgebgeben, wenn die Nutzereingabe in einem Chat gespeichert werden konnte und das RAG eine Antwort gebaut hat.

Dies Ausgabe enthält u.a. die Antwort des RAG.
```json
{
    "content": "Platzhalter",
    "conversation_id": 1,
    "message_id": 4,
    "metadata": {},
    "role": "assistant",
    "timestamp": "2025-11-28T09:17:00.370961"
}
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
Wird in folgenden Fällen ausgegeben:

#### Fehler beim Speichern der Nutzereingabe
Wenn die Nutzereingabe nicht gespeichert werden konnte, wird diese Nachricht ausgegeben:

```
Could not save user-message!
```

#### Fehler beim Generieren der RAG-Ausgabe
Falls das RAG keine Antwort liefert, wird folgende Nachricht ausgegeben:
```
Could not generate assistant-message!
```
