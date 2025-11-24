# Backend API-Dokumentation (`/api/accounts`)
## GET `/api/accounts`
Gibt Nutzerdaten zum aktuellen Nutzer der aktiven Session zurück.

Hierfür wird eine aktive Session benötigt!

### Response 200
```json
{
    "accountId": "838b4559-bacf-494a-8d35-2cb4af29dcb4",
    "createdAt": "Mon, 24 Nov 2025 14:31:59 GMT",
    "displayName": "test@test.com",
    "displayNameUpdatedAt": "Mon, 24 Nov 2025 14:31:59 GMT",
    "email": "test@test.com",
    "emailUpdatedAt": "Mon, 24 Nov 2025 14:31:59 GMT",
    "passwordUpdatedAt": "Mon, 24 Nov 2025 14:31:59 GMT"
}
```

### Response 401 (No active session)
```
```

## POST `/api/accounts/login`
Meldet den Nutzer mit Benutzername und Passwort an.
Dies schlägt fehl, sofern Benutzername und Passwort nicht übereinstimmen, oder kein Nutzer mit diesem Nutzernamen existiert.

Sofern bereits ein Session-Token vorliegt, wird dies **immer** entfernt, ganz egal, ob die angegebenen Nutzerdaten valide sind!

### Request-Body
```json
{
    "username": "test",
    "password": "test"
}
```

### Response 200
```
Valid credentials
```
Zudem wird ein JWT-Token als Cookie bereitgestellt!

### Response 400 (User not found/Invalid Credentials)
```
Invalid credentials
```


## GET `/api/accounts/logout`
Meldet den aktuell angemeldeten Nutzer ab.
Die aktuelle Session wird aufgelöst.

Hierfür muss der Nutzer angemeldet sein.

### Response 200
```
Successfully logged out!
```

### Response 401 (Unauthorized)
```
```

## POST `/api/accounts/register`
Erstellt einen neuen Nutzer.
Der Benutzername darf dabei nicht mit einem anderen Nutzer übereinstimmen.

Es wird kein Anmeldeverfahren eingeleitet.
Ein Session-Token wird nicht vergeben.

### Request-Body
```json
{
    "username": "test",
    "password": "test"
}
```

### Response 200
```
{
    "accountId": "838b4559-bacf-494a-8d35-2cb4af29dcb4",
    "createdAt": "Mon, 24 Nov 2025 14:31:59 GMT",
    "displayName": "test@test.com",
    "displayNameUpdatedAt": "Mon, 24 Nov 2025 14:31:59 GMT",
    "email": "test@test.com",
    "emailUpdatedAt": "Mon, 24 Nov 2025 14:31:59 GMT",
    "passwordUpdatedAt": "Mon, 24 Nov 2025 14:31:59 GMT"
}
```

### Response 400 (Username already in use)
```
Username is already in use! Sorry :(
```