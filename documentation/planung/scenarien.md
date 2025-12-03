# Szenarien

### Mögliche Datentypen:
* Strukturiert
* Semi-Strukturiert
* Embeddings
* Ephemerer Zustand
* Zeitreihen

### Zugriffsmethoden
* Read-Heavy
* Write-Heavy
* R/W-Heavy
* Append only
* Bulk ingest
* ULL Key/Value


## Kundendaten
Speicherung von Kundenbezogenen Daten

* strukturiert
* R/W-Heavy
* Merkmale
    + erfordert Konsistenz
    + kritisch

## Messwerte
* Zeitreihe
* write-heavy | append-only
* Merkmale
    + n/a

## Logging
* Zeitreihe
* write-heavy

## Produktbestände
* strukturiert
* r/w heavy
* Merkmale
    + erfordert Konsistenz
    + kritisch

## Dokumentchunks
* semi-strukturiert
* read-heavy

## Chatverlauf
* semi-strukturiert
* append only

## Sessionmanagement
* Ephemerer Zustand
* ULL Key/Value Store
* Merkmale:
    + muss sehr kurze Latenzen haben (<10ms)
    + kritisch

## Embeddings
* embedding
* r heavy
* Merkmale
    + Vektorsuche
