1. Ziel des Moduls
Nach diesem Modul kannst Du:

begründen, warum die Vektor-Datenbank kein architektonischer Wunsch, sondern ein Performance-Zwang ist, um Dein P95-Latenz-SLO einzuhalten.

die logische Inkompatibilität von herkömmlichen B-Trees und den benötigten Vektor-Indizes verstehen.

Dein Vektor-Schema für das Pre-Filtering der Metadaten entwerfen.

Hier kommen ein paar Vermutungen, die es dann in der Labor-Aufgabe zu überprüfen gilt! (d.h. hier sind so typische "Blog-post Aussagen" die alle wiederholen, ohne sie kritisch zu hinterfragen - genau das tun wir dann in der Laboraufgabe!

2. Warum Dein 500 ms SLO die Trennung Erzwingt
Du hast in Modul 4.5 gelernt, dass Dein P95 Latenz-Budget für die Approximate Nearest Neighbor (ANN)-Suche nur ≤50 ms beträgt. Dieser Wert zwingt Dich zur Workload-Isolation und zur Nutzung einer Polyglotten Architektur.

Der Workload-Konflikt: Die ANN-Suche ist eine CPU-intensive Operation, die Distanzberechnungen für Tausende von Vektoren durchführt. Würdest Du diese Last auf Deinen MongoDB-Instanz legen, die für Deine konsistenten Chunk-Lookups (Modul 5) zuständig ist, würde die CPU überlastet. Die Latenz beider Systeme würde sofort einbrechen und Dein 500 ms SLO wäre gerissen.

Die Schlussfolgerung: Um die Workload-Isolation und die Latenzgarantie zu gewährleisten, musst Du einen dedizierten Vektor-Store verwenden, um das ≤50 ms Budget zu isolieren.

3. Logische Inkompatibilität: B-Trees vs. Vektor-Index
Deine traditionellen Datenbanken (SQL, MongoDB) nutzen B-Trees. B-Trees sind ideal für Ordnungsrelationen(A<B) und punktuelle Gleichheit (A=’ID’).

Die ANN-Suche sucht jedoch Nachbarschafts- und Distanzrelationen (VektorA ist dem VektorB ähnlich).

Der Grund: Ein B-Tree müsste jeden einzelnen Vektor durchsuchen, um die kürzeste Distanz zu finden. Dies ist die Exakte Nächste Nachbarsuche (NNS) – sie ist präzise, aber viel zu langsam für ≤50 ms.

Die Lösung: Spezialisierte Vektor-Indexe wie HNSW (Hierarchical Navigable Small Worlds) opfern Genauigkeit (Recall) für Geschwindigkeit (Latenz), indem sie die Suche auf eine kleine Untermenge beschränken.

4. Das Vektor-Schema und der Latenz-Beweis
Da die Index-Entscheidung Deine Latenz bestimmt, musst Du Dein Vektor-Schema auf die 50 ms ausrichten. Das Modell muss minimalistisch sein und die Referenz-Logik (Modul 5) sauber umsetzen.

A. Vektor-Schema (Das Small Document)
Dein Vektor-Dokument im Vektor-Store (pgvector oder Mongo Atlas) ist kompakt:

Feld	Typ	Zweck
embedding_id (PK)	String	Die Referenz-ID zu Deinem Chunk-Dokument (Modul 6).
vector	Float Array	Der eigentliche Vektor (z.B. 768 Dimensionen).
Metadaten	String / Int	Metadaten für das Pre-Filtering (z.B. product_family).
B. Metadaten-Nutzung und Pre-Filtering
Die Metadaten (z.B. product_family) sind Dein Schlüssel, um die 50 ms Latenz zu halten:

Pre-Filtering: Anstatt die ANN-Suche über alle Vektoren laufen zu lassen, nutzt Du die Metadaten, um den Suchraum vorab einzuschränken.

Beispiel-Query: "Finde die 5 ähnlichsten Chunks NUR in der Produktfamilie 'KA-22'." Diese Operation wird zuerst als schneller Filter im Vektor-Store ausgeführt und reduziert die Anzahl der notwendigen Distanzberechnungen drastisch, was das 50 ms Budget schützt.

C. Der Latenz-Hebel: Index-Tuning
Der HNSW-Index wird mit Parametern wie M und ef konfiguriert. Dies ist der erste nicht-deterministische Teil Deiner Architektur, da die Wahl dieser Parameter die Latenz gegen die Genauigkeit (Recall) abwägt.

Aktionspunkt: Im Praxismodul 4.5 wirst Du durch das Tuning dieser Parameter messen, wie Du die Latenz (z.B. 60 ms→45 ms) verbesserst, um Dein Budget einzuhalten.

5. Capstone-Checkliste (Modul 7)
Um die Eignung Deines Vektor-Modells für die Produktionsfreigabe zu beweisen, müssen diese Punkte in Deiner Dokumentation enthalten sein:

Architekturentscheidung: Die Nutzung eines dedizierten Vektor-Stores (z.B. pgvector) ist begründet mit dem ≤50 ms Latenz-Budget und dem Workload-Konflikt. (nicht nur sagen, dass es so ist (blog-post Aussage), sondern belegt durch Messungen.

Modell-Definition: Das Vektor-Schema ist als Small Document definiert und enthält nur die zur Suche zwingend notwendigen Felder plus die Metadaten für das Pre-Filtering.

Referenz-Logik: Die Verknüpfung zwischen dem Vektor-Store (embedding_id) und dem Document Store (chunk_id) ist klar definiert.

Index-Tuning-Plan: Du hast die Notwendigkeit des HNSW-Index-Tunings (Anpassung von M/ef) gemessen und dokumentiert, um das 50 ms Budget unter Peak-Last einzuhalten.

6. Quick-Check – Prüfe Dein Verständnis
Bist Du in der Lage, zu erklären, warum ein B-Tree die 50 ms Latenz bei der ANN-Suche niemals einhalten kann?

Kannst Du begründen, warum die Metadaten für das Pre-Filtering im Vektor-Schema gespeichert werden müssen, obwohl die Hauptdaten in MongoDB liegen?

Verstehst Du, dass die Wahl des HNSW-Indexes ein bewusst ungenaues (nicht-deterministisches) Element in der Architektur ist, das die Geschwindigkeit garantiert?

Wenn ja → weiter zu Modul 8: Retrieval-Strategien und Metadaten-Nutzung.