# Backend API-Dokumentation (`/api/chats`)
## GET `/api/chats`
Gibt Titel und ID alles CHats des aktuell angemeldeten Nutzers zurück.

Hierfür muss der Nutzer angemeldet sein.

### Response 200
```json
[
    {
        "chatId": "eadf51c4-b531-43e9-96b9-310f6c903251",
        "chatTitle": "New Chat"
    }
]
```

### Response 401 (Unauthorized)
```
```

## GET `/api/chats/<chat_id>`
Gibt alle zu dem angegeben Chat gehörende Informationen zurück.
Der Chat wird durch die `chat_id` identifiziert.

Hierfür muss der Nutzer angemeldet sein.

**Hinweis**: Dokumente sind noch nicht enthalten!

### Response 200
```json
{
    "accountId": "838b4559-bacf-494a-8d35-2cb4af29dcb4",
    "chatId": "eadf51c4-b531-43e9-96b9-310f6c903251",
    "chatTitle": "New Chat",
    "createdAt": "Mon, 24 Nov 2025 14:32:27 GMT",
    "messages": [
        {
            "files": [],
            "role": "user",
            "text": "Meine Nachricht"
        },
        {
            "files": [],
            "role": "assistent",
            "text": "Meine Nachricht"
        }
    ]
}
```

### Response 401 (Unauthorized)
```
```

### Response 404 (Resource not found)
```
Chat with chat_id '{chat_id}' not found!
```