# Backend Dokumentation

Das ist die Dokumentation für das Python-Backend des RAG-Systems

## Übersicht
- [Backend mit Flask](#backend-mit-flask)
- [Authentifizierung](#authentifizierung)
    - [Erstellung und Aufbau eines Session-Tokens](#erstellung-und-aufbau-eines-session-tokens)
    - [Speicherung des Session-Tokens](#speicherung-des-session-tokens)
    - [Löschung des Session-Tokens](#löschung-des-session-tokens)
- [Datenbankzugänge](#datenbankzugänge)
- [Objekte](#objekte)
    - [Umwandlungsbedürftige Objekte](#umwandlungsbedürftige-objekte)
- [Hochgeladene Dateien](#hochgeladene-dateien)

## Backend mit Flask
Das Backend verwendet Flask um die Endpunkte zu Nutzen.

Für alle Endpunkte kann die Dokumentation in [api-documentation.md](./api/api-documentation.md) nachvollzogen werden.

## Authentifizierung
Für etwaige Endpunkte ist eine Authentifizierung notwendig.
Diese erfolgt mithilfe eines Session-Cookies.
Das Session-Cookie enthält die `session_id` der aktiven Sitzung.

Ohne dieses Session-Cookie werden alle Anfragen auf bestimmte Enpunkte mit `401 - Unauthorized` beantwortet.

### Erstellung und Aufbau eines Session-Tokens
Damit ein Session-Token erstellt wird, muss ein Nutzer sich erfolgreich anmelden.
Ein Session-Token hat folgenden Aufbau:
```json
{
    "session_id": <uuid>,
    "user_id": <int>,
    "created_at": <datetime.datetime>,
    "expires_at": <datetime.datetime>
}
```

Die `session_id` wird mithilfe der `uuid` Bibliothek generiert.
Diese ist im Session-Cookie enthalten.

Die `user_id` ist die numerische ID des Nutzers.
Dabei handelt es sich um einen inkrementellen Wert.

Der `created_at` Zeitstempel gibt an, wann das Session-Token ausgestellt wurde.

Der `expires_at` Zeitstempel gibt an, wann das Session-Token auslaufen wird wurde.

<br>

Mit jeder authentifizierten wird der `expires_at` Zeitstempel aktualisiert.
Dieser beifndet sich 1 Tag in der Zukunft.

### Speicherung des Session-Tokens
Das Session-Token wird in einer Redis-Datenbank gespeichert.

Hierbei wird der Inhalt des Session-Tokens in einem Hash gespeichert.
Dieser Hash wird unter dem `session:<session_id>` Schlüssel gespeichert.

Des Weiteren sind diese Einträge mit einem `Time-To-Life` versehen.
Damit laufen diese nach 10min ab.
Dieses TTL wird aber mit jeder neuen Anfrage erneuert.

### Löschung des Session-Tokens
Sollte das Session-Token auslaufen, oder der Nutzer sich abmelden, so wird das Session-Token invalidiert.

Hierzu wird dieses aus der Redis-Datenbank entfernt.
Das Session-Cookie wird beim Nutzer auch entfernt.


## Datenbankzugänge
Das Backend greift direkt auf die Datenbanken zu.
Für jede Datenbank gibt es einen eigenen Client bzw. Context-Manager.

An den benötigten Stellen werden direkt Befehle an die Datenbanken geschickt.

**Hinweis**: Das RAG ist nicht SQL-Injection geschützt.
Das liegt daran, dass dies für ein Studentenprojekt nicht unbedingt notwendig ist und nur unnötig Zeit frisst.


## Objekte
Für viele Objekte in den Datenbanken gibt es äquivalente Klassen.
Diese sind idR. `dataclasses` und Verfügen über Methoden um zwischen einem Objekt und einem Dictionary zu wechseln.


### Umwandlungsbedürftige Objekte
Bestimmte Objekte haben Attribute, welche nicht ohne weiteres in der Form an das Frontend übermittelt werden können.

#### Zeitstempel
Viele Objekte sind an einen Zeitstempel gebunden.
Dieser wird in der PostgresDB auch als soclher gespeichert.

Für das Frontend sind diese aber nicht nützlich.
Darum werden diese in das ISO-Format konvertiert (YYYY-MM-DDThh:mm:ss.\<ms>).

#### UUIDs
Für bestimmte Objekte werden UUIDs vergeben.
Innerhalb des backends werden diese auch als solche verwendet.

Für das Frontend sind diese aber nicht nützlich.
Darum werden diese in einen String umgewandelt.


## Hochgeladene Dateien
Das Backend erlaubt es dem Nutzer Dateien in Chats hochzuladen.

Diese werden in der PostgresDB referenziert und in dem `/upload` Verzeichnis gespeichert. Die Dateien haben dabei die `file_uuid` als Namen ohne Dateiendung.