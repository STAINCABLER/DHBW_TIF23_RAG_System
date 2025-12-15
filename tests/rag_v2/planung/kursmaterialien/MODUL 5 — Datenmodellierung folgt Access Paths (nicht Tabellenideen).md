In Modul 4 hast du gelernt, wie man Query Paths identifiziert und bewertet.
Du weißt jetzt:

welche Schritte eine Anfrage im System durchläuft,

welche davon kritisch sind (→ beeinflussen die Antwortzeit),

welche davon nicht kritisch sind (→ dürfen langsam sein),

welche Datenbanken in diesen Pfaden liegen,

welches Latenzbudget diese Pfade haben.

In Modul 5 geht es darum, aus diesen Query Paths das tatsächliche Datenmodell zu bauen.

Du lernst:

wie man aus einem Query Path ein konkretes Dokument- oder Tabellenmodell ableitet,

wann man Daten zusammen in ein Dokument packt (embed),

wann man sie lieber trennt (reference),

wie man Roundtrips vermeidet,

wie man Dokumentgrößen wählt,

und wie man Datenmodelle so strukturiert, dass sie den kritischen Pfad optimieren.

Modul 5 beantwortet also die Frage:

👉 „Wie muss ich die Daten physisch strukturieren, damit meine wichtigsten Queries schnell sind?“
Zusammengefasst:
Modul 4 = verstehen, welche Pfade kritisch sind
(Analyse der Zugriffswege und Latenzen)

Modul 5 = das Modell so designen, dass diese Pfade optimal laufen
(Access-Path-basierte Datenmodellierung)

Beide Module gehören zusammen.

Modul 4 zeigt dir, was das System tun muss.
Modul 5 zeigt dir, wie du deine Daten dafür strukturierst.


1. Ziel des Moduls
Nach diesem Modul kannst du:

erkennen, warum Datenmodelle aus Queries entstehen, nicht aus „Feldern“,

Access-Path-basierte Modellierung anwenden,

entscheiden, wann ein Dokument groß/klein sein sollte,

entscheiden, wann man Daten embedden und wann referenzieren sollte,

Roundtrips vermeiden,

ein dokumentenorientiertes Datenmodell für deinen Capstone erstellen.

Dieses Modul ist die Basis für alles, was danach kommt: Chunking, Embeddings, Metadaten, Retrieval.

2. Der wichtigste Paradigmenwechsel
Falsch (klassisch, SQL-Denke):

„Ich baue erst Tabellen, dann schreibe ich Queries.“

Richtig (professionelles Data Engineering):

„Ich definiere zuerst die Queries, dann baue ich das Datenmodell.“

Warum?

Weil Latenz, Kosten und Skalierung immer aus den Query Paths kommen — nie aus der „Datenstruktur an sich“.

3. Kernprinzip: Access Paths bestimmen das Modell
Ein Access Path ist:

welche Daten,

in welcher Reihenfolge,

aus welchen Objekten,

mit welcher Latenz,

für welche Operation

gelesen werden müssen.

Dein Modell muss genau diese Paths optimieren — nicht mehr, nicht weniger.

Merksatz:

Ein gutes Dokumentenmodell ist ein Replikat deiner Query Paths.

4. Drei Modellierungsentscheidungen, die alles bestimmen
Wenn du ein NoSQL-/Dokumentenmodell baust, entscheidet genau Folgendes:

4.1 EMBED vs REFERENCE
Embed, wenn:

du immer alles gemeinsam liest

die Daten klein sind

du Roundtrips vermeiden willst

Konsistenz nicht kritisch ist

Reference, wenn:

separate Updates nötig sind

Daten groß sind

Objekt eigenständige Lebenszyklen hat

Konsistenz wichtig ist

4.2 Big Documents vs Small Documents
Große Dokumente, wenn:

du fast immer das ganze Ding brauchst

wenig Update-Druck besteht

du Latenz minimieren willst

Kleine Dokumente, wenn:

du nur Teilmengen liest

das Objekt häufig aktualisiert wird

du breitere Slices brauchst (z. B. nach Kategorie)

4.3 Precompute vs Compute-on-Read
Precompute, wenn:

Query im kritischen Pfad

Sort/Filter teuer

viele Reads / wenige Writes

Compute-on-Read, wenn:

Daten winzig

wenige Aufrufe

Berechnung trivial




Fallstudie – Median-Lieferzeit 
Ziel: An diesem Beispiel siehst Du, wie man komplett aus dem Access Path und den drei Modellierungsentscheidungen das richtige Datenmodell ableitet.

1. Access Path (Schritt für Schritt)
Fragestellung:
„Wie hoch ist die mediane Lieferzeit für eine Produktkategorie im letzten 30-Tage-Fenster?“

Access Path:

Finde alle Lieferereignisse der letzten 30 Tage.

Berechne die Lieferdauer je Ereignis.

Sortiere alle Lieferdauern.

Nimm den mittleren Wert → Median.

Der Median kann nur berechnet werden, wenn alle Einzelwerte vorhanden sind.

2. Die drei Modellierungsentscheidungen (wie in Modul 5)
4.1 EMBED vs. REFERENCE
❌ EMBED (falsch)
Beispiel für eine schlechte Modellierung:

{
  "product_id": 123,
  "category": "Coffee Machines",
  "deliveries": [
    { "delivery_id": 1, "shipped_at": "...", "delivered_at": "..." },
    { "delivery_id": 2, "shipped_at": "...", "delivered_at": "..." }
    // viele weitere
  ]
}
Probleme:

sehr große Dokumente

schwer indexierbar

Sortierung in Arrays teuer

das ganze Dokument muss für jede Berechnung geladen werden

✔️ REFERENCE (richtig)
Eine Lieferung = ein einzelnes Dokument/Objekt.

{
  "delivery_id": 924881,
  "product_id": 123,
  "category": "Coffee Machines",
  "shipped_at": "2025-03-01T10:00:00Z",
  "delivered_at": "2025-03-05T09:12:00Z",
  "delivery_days": 3.96
}
Vorteile:

sauber filterbar

gut indexierbar

ideale Basis für Sortierung

kein Dokumentwachstum

Ergebnis: Für Median-Berechnung ist REFERENCE zwingend.

4.2 Big Document vs. Small Document
❌ Big Document (falsch)
Beispiel:

{
  "category": "Coffee Machines",
  "delivery_stats": {
    "durations_last_30_days": [2.1, 4.0, 3.9, 6.2, ...]
  }
}
Probleme:

arrays werden riesig

Sortierung findet im Dokument statt

vollständig laden → hohe Latenz

Updates blockieren sich gegenseitig

✔️ Small Document (richtig)
Small Documents:

flache Struktur

1 Ereignis = 1 Dokument

sehr gut indexierbar

kein wachsendes “Mega-Dokument”

Ergebnis: Median-Berechnung funktioniert nur mit vielen kleinen Dokumenten.

4.3 Precompute vs. Compute-on-Read
❌ Compute-on-Read (falsch)
Jede Anfrage müsste:

alle Lieferungen laden

sortieren

Median berechnen

→ sehr teuer
→ langsam
→ hohe Serverlast

✔️ Precompute (richtig)
Median wird zyklisch im Hintergrund berechnet.
Abfrage braucht nur noch einen einzigen Wert.

Vorteile:

schnelle Antwortzeiten

kritischer Pfad minimal

gut skalierbar

Ergebnis: Median muss precomputed werden.

3. Das daraus abgeleitete Datenmodell
3.1 Tabelle für Lieferereignisse
CREATE TABLE deliveries (
  delivery_id     bigserial PRIMARY KEY,
  product_id      bigint NOT NULL,
  category        text   NOT NULL,
  shipped_at      timestamptz NOT NULL,
  delivered_at    timestamptz NOT NULL,
  delivery_days   numeric GENERATED ALWAYS AS
       ((EXTRACT(EPOCH FROM delivered_at - shipped_at)/86400)) STORED
);

CREATE INDEX idx_deliveries_category_time
  ON deliveries (category, shipped_at);
3.2 Materialized View für den Median
CREATE MATERIALIZED VIEW mv_median_delivery AS
SELECT category,
       percentile_cont(0.5)
         WITHIN GROUP (ORDER BY delivery_days) AS median_delivery_days
FROM deliveries
WHERE shipped_at > now() - interval '30 days'
GROUP BY category;
4. Kritischer Pfad (Modul 4 Bezug)
Query Path:

SELECT median_delivery_days
FROM mv_median_delivery
WHERE category = 'Coffee Machines';
Warum dieser Pfad kritisch ist:

wird häufig aufgerufen

muss schnell sein

Sortierung darf nicht im Pfad liegen

kleiner Lookup statt großer Array-Operation

Datenmodell unterstützt diesen Pfad durch:

Small Documents

Reference-Modell

Index auf Zeitfenster

Precompute




Latenz in diesem Szenario
Die drei Modellierungsentscheidungen reduzieren die Latenz im kritischen Pfad:

Modellierungsform	Latenz pro Anfrage	Problem
Compute-on-Read (Sortierung)	80–300 ms	zu langsam für Dashboards
Big Document (500 KB – 2 MB)	20–50 ms	Transfer + Parsing zu teuer
Small Documents + Index	5–10 ms	optimal
Precompute (Materialized View)	3–5 ms	perfekter kritischer Pfad



5. Check-Dein-Verständnis
Kannst Du für dieses Beispiel:

EMBED vs. REFERENCE korrekt begründen?

Big Document vs. Small Document unterscheiden?

Precompute vs. Compute-on-Read erklären?

zeigen, wie genau der Access Path das Modell bestimmt?




6. Access-Path-Mapping für dein Capstone
Für jedes deiner Objekte musst du beantworten:

6.1 Welche Queries lese ich IMMER?
Wenn 90 % der Queries dieselben Felder laden → EMBED.

6.2 Welche Queries liegen IM CRITICAL PATH?
Diese müssen die wenigsten Roundtrips haben.

6.3 Welche Daten wachsen schnell?
Große Arrays → manchmal splitten.

6.4 Welche Daten werden häufig aktualisiert?
Große Dokumente mit Updates → schlecht.

6.5 Welche Daten passen gut in ein Dokument?
Z. B. alle Chunk-Metadaten.

6.6 Welche müssen separat versioniert werden?
z. B. Kundenprofile.

7. Häufige Modellierungsfehler (bewertungsrelevant)
Zu große Dokumente: 300 kB PDFs in Mongo speichern

Zu kleine Dokumente: 1 Satz pro Dokument

Metadaten vergessen (section_title, position)

embedding ins Chunk speichern → unnötig groß

Chat als 1 Dokument pro Nachricht → 1000 Roundtrips

Mongo nutzen für ACID-Operationen

Referenzen nutzen, obwohl kein Update nötig ist

8. Bezug zum Capstone (explizit prüfrelevant)
In deiner Ausarbeitung muss stehen:

Welche Access Paths dein System hat

Wie du daraus konkret dein Datenmodell abgeleitet hast (und wie es die Latenzen adressiert)

Warum EMBED/REFERENCE gewählt wurde

Warum deine Dokumentgröße sinnvoll ist

Wie dein Modell kritische Pfade minimiert 

Welche Risiken du bewusst ausgeschlossen hast

Wenn du das nicht explizit dokumentierst, gilt das Modell als nicht begründet.