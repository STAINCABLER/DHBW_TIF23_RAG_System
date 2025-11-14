# Backend API-Dokumentation (`/api/chats`)
## GET `/api/chats`
Gibt Titel und ID alles CHats des aktuell angemeldeten Nutzers zurück.

Hierfür muss der Nutzer angemeldet sein.

### Response 200
```json
[
    {
        "chat_id": "552cd66f-52af-473a-9f9d-55771d6126fa",
        "title": "Testtitel"
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
    "chat_id": "552cd66f-52af-473a-9f9d-55771d6126fa",
    "title": "Testtitel",
    "entries": [
        {
            "question": "Frage",
            "response": "Response"
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