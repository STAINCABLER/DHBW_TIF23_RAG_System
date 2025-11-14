# Backend API-Documentation
## GET `/api`
Gibt alle existierenden Endpunkte mit ihren Parameters und HTTP-Methoden zurück.

Benötigt keine aktive Session.

### Response 200
```json
[
    {
        "path": "/exmaple/<param>/path",
        "method": "GET",
        "parameter": [
            "param"
        ]
    }
]
```
