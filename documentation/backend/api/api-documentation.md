# API Dokumentationsueberblick

Dieses Dokument liefert eine orientierende Einfuehrung in die backendseitige REST-API des RAG-Systems. Detaillierte Informationen zu einzelnen Endpunkten, Request- und Response-Schemata sowie Fehlercodes finden sich in den verlinkten Unterkapiteln der Projektdokumentation.

- **Zielgruppe**: Entwicklerinnen und Entwickler, die das Backend integrieren oder erweitern, sowie technische Stakeholder.
- **Authentifizierung**: Der Zugriff auf geschuetzte Routen erfolgt ueber Session Tokens, die nach erfolgreichem Login erzeugt und bei jedem Folge-Request mitgesendet werden muessen.
- **Versionierung**: Die API steht derzeit als stabile Hauptversion ohne expliziten Versionspfad bereit. Breaking Changes werden durch Release Notes in der Projektdokumentation angekuendigt.

## Funktionsbereiche

- **Accounts**: Verwaltung von Nutzerdaten, Registrierung, Login und Logout.
- **Chats**: Zugriff auf bestehende Konversationen und das Einstellen neuer Fragen an das RAG-System.
- **Dokumente**: Hochladen, Listen, Abrufen und Entfernen von Wissensdokumenten (PDF, Text, CSV, JSON) fuer das Retrieval.
- **Systemuebersicht**: Der Root-Endpunkt stellt eine maschinenlesbare Liste aller verfuegbaren Routen bereit und eignet sich fuer einfache Health-Checks.

## Aufbau der Detaildokumentation

1. **Einleitung und Authentifizierung**: Rahmenbedingungen, Sicherheitsaspekte und typische Header.
2. **Endpoints je Domain**: Beschreibung der HTTP-Methoden, Parameter, Beispiel-Requests und Responses.
3. **Fehlerbehandlung**: Auflistung der standardisierten Statuscodes und Fehlermeldungen.
4. **Beispielablaeufe**: Typische Integrationsszenarien wie Registrierung, Session-Verwaltung oder Chat-Interaktionen.

## Endpunktuebersicht

- `/api` – Gesamtuebersicht der verfuegbaren Routen und Health-Check ([Details](./api-docs.md))
- `/api/accounts` – Registrierung, Login, Logout und Nutzerverwaltung ([Details](./api-accounts-docs.md))
- `/api/chats` – Abruf bestehender Chats und Stellen neuer Fragen ([Details](./api-chats-docs.md))
- `/api/docs` – Dokumentverwaltung fuer das Wissens-Backend ([Details](./api-docs-docs.md))

## Weiteres Vorgehen

Fuer einen schnellen Einstieg empfiehlt sich folgende Reihenfolge:

1. Authentifizierungsflow verstehen und Session Token generieren.
2. Bestehende Chat-Daten abrufen, um die Struktur der Antworten kennenzulernen.
3. Eigene Dokumente hochladen und neue Anfragen ueber die Chat-Routen ausfuehren.

Bei Fragen zur Implementierung oder zu speziellen Use Cases helfen die themenspezifischen Kapitel sowie der direkte Austausch mit dem Backend-Team.
