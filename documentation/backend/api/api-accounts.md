# Backend API-Dokumentation (`/api/accounts`)
Alle mit * markierten Anfragen benötigen eine aktive und gültige Session.
Andernfalls wird eine `401 - Unauthorized` zurückgegeben!

## Endpunkte
- GET [`/api/accounts`](#get-apiaccounts)*
- POST [`/api/accounts/login`](#post-apiaccountslogin)
- GET/POST [`/api/accounts/logout`](#getpost-apiaccountslogout)*
- POST [`/api/accounts/register`](#post-apiaccountsregister)


## GET `/api/accounts`*

Ausgabe von ausgewählten Benutzerdaten.
Dies beeinhaltet alles außer den Passwort-Hash.

### Response `200 - OK`
Wird ausgegeben, sofern der Nutzer der aktiven Session existiert.

```json
{
  "created_at": "2025-11-28T08:31:26.435701",
  "email": "user@dhbw.de",
  "id": 1,
  "is_active": true,
  "last_login": "2025-11-28T13:00:05.462263",
  "profile_type": "student",
  "username": "user"
}
```

### Response `401 - Unauthorized`
Wird ausgegeben, falls keine aktive & gültige Session vorliegt, oder der Nutzer dieser Session nicht existiert.

In beiden Fällen wird eine leere Antwort mit Status-Code `401` gesendet.


## POST `/api/accounts/login`
Meldet den Nutzer mit den angegebenen Anmeldedaten an.
Zurückgegeben wird ein Session-Cookie (JWT von Flask).

Sofern der Nutzer schon über ein Session-Token verfügt, wird das bestehende entfernt und ungültig gemacht.
Dies betrifft nur das Session-Token, welches mit der Login-Anfrage mitgesandt wurde.
Andere Sessions auf anderen Geräten oder Browsern bleiben bestehen.

### Request-Body
```json
{
    "email": "user@dhbw.de",
    "password": "password"
}
```

- `email`: E-Mail Adresse des Nutzers
- `password`: Passwort des Nutzers

### Response `200 - OK`
Unter folgenden Bedingungen wird der Nutzer angemeldet:
- Ein Nutzer mit angegebener E-Mail Adresse existiert
- Passwort stimmt mit dem gespeicherten Passwort überein
- Der Nutzer ist nicht deaktiviert

In diesem Fall wird folgende Nachricht zurückgegeben:
```
Successfully logged in!
```

Zudem wird ein Session-Token als Cookie übertragen.
Dieses verweist auf eine session_id, welche zusätzlich in einer Redis-Datenbank gespeichert wird.

Des Weiteren wird in der PostgresDB der `last_login`-Zeitstempel des Nutzers auf den aktuellen Zeitstempel aktualisiert.

### Response `400 - Bad Request`
In allen nicht im vorherigen Abschnitt abgedeckten Fällen wird diese Antwort ausgegeben.

Dies betrifft vor allem den Fall, bei welchem die Zugangsdaten nicht stimmen.
```
Invalid credentials
```


## GET/POST `/api/accounts/logout`*
Meldet den Nutzer ab und invalidiert das Session-Token.

Diese Anfrage ist sowohl als GET- als auch als POST-Anfrage möglich.
Im Falle einer POST Anfrage muss diese keinen Body beeinhalten.

### Response `200 - OK`
Wird ausgegeben, sofern der Nutzer eine aktive & gültige Session hat und erfolgreich abgemeldet wurde.

Hierbei wird das Session-Token invalidiert und das Session-Cookie entfernt.

### Response `401 - Unauthorized`
Wird ausgegeben, falls keine aktive & gültige Session vorliegt

In diesen Fall wird eine leere Antwort mit Status-Code `401` gesendet.


## POST `/api/accounts/register`
Registriert einen neuen Benutzer mithilfe einer E-Mail und eines Passwortes.

Hierduch wird ein Nutzer zwar hinterlegt, er wird aber nicht automatisch in eine aktive Session gesetzt. Dies muss separat geschehen.

### Request-Body
```json
{
    "email": "user@dhbw.de",
    "password": "password"
}
```

- `email`: E-Mail Adresse des Nutzers
- `password`: Passwort des Nutzers


### Response `201 - Created`
Wird ausgegeben, wenn der Nutzer erfolgreich erstellt wurde.
Der Nutzer wurde damit in der PostgresDB hinterlegt und kann sich ab nun anmelden.

```
User successfully created!
```


### Response `400 - Bad Request`
Der Status-Code 400 kann in mehreren Fällen zurückgegeben werden:

#### Fehlerhaft Eingabedaten
Wird ausgegeben, wenn keine E-Mail Adresse oder kein Passwort angeben wurde.

```
Email and password are required!
```

#### E-Mail Adresse bereits in Verwendung
Wird ausgegeben, wenn bereits ein Nutzer mit dieser E-Mail Adresse existiert.

```
Email is already taken!
```