## 📘 Erfahrungsbericht zum Projekt: Social-Media-Datenanalyse mit MLOps-Integration

Natürlich – hier ist dein überarbeiteter Text in einer klareren, professionelleren und stilistisch runderen Fassung. Ich habe dabei sowohl den Ton als auch den Aufbau leicht angepasst, ohne deinen persönlichen Stil zu verlieren:


### Einleitung

Mein Projekt begann offiziell am 13. März 2025. Der Einstieg war herausfordernd: Ich war zunächst unentschlossen, welches Thema ich verfolgen sollte. Wichtig war mir, ein Vorhaben zu wählen, das sowohl persönliches Interesse weckt als auch gesellschaftliche Relevanz besitzt – abseits der gängigen Standardprojekte.

Ursprünglich plante ich eine Analyse von Symptomen im Bereich neurodivergenter Erkrankungen. Dieses Thema hätte zwar großes Potenzial geboten, erwies sich jedoch aufgrund unzureichender öffentlich zugänglicher Datenquellen als kaum umsetzbar. In Absprache mit Prof. Dr. Klotz orientierte ich mich daher neu – hin zu einer datengetriebenen Analyse von Trends auf sozialen Medien.

Ab diesem Zeitpunkt nahm das Projekt konkrete Formen an, allerdings war bereits wertvolle Zeit vergangen. Um den Projektverlauf besser einordnen zu können, folgt eine grobe zeitliche Einordnung:

#### Zeitübersicht

| Zeitraum        | Schwerpunkt                                            |
| --------------- | ------------------------------------------------------ |
| 17.03. – 23.03. | Beruflicher Fokus, kein Fortschritt am Projekt         |
| 24.03. – 30.03. | Beruflicher Fokus, kein Fortschritt am Projekt         |
| 31.03. – 06.04. | Themenfindung                                          |
| 07.04. – 13.04. | Umorientierung auf Social-Media-Trendanalyse           |
| 14.04. – 20.04. | Erste Scraping-Skripte, Test verschiedener Plattformen |
| 21.04. – 27.04. | Versuch der Automatisierung mit Render                 |
| 28.04. – 04.05. | Fehlerbehebung bei automatisiertem Scraping\*          |
| 05.05. – 11.05. | Daten sammeln, bereinigen und zusammenführen           |
| 12.05. – 17.05. | Modellierung, Evaluierung, Dokumentation               |

\* Das Scraping lief zu diesem Zeitpunkt lokal bereits stabil. Nach dem Deployment auf Render zeigte sich jedoch, dass der TikTok-Scraper dort nicht mehr funktionierte – vermutlich wegen der Architektur der inoffiziellen API. Daher entschied ich mich für eine hybride Lösung mit lokalem Scraper und serverseitiger Verarbeitung.

Diese Übersicht verdeutlicht, wie stark der Erfolg des Projekts von einer stabilen Datenbasis abhängig war – und wie viel Zeit für deren Aufbau erforderlich war. Die kontinuierliche Anpassung des Scraping-Prozesses war dabei die größte Herausforderung: Immer wieder musste ich Teile der Architektur überarbeiten oder zurückrollen, wodurch auch Inkonsistenzen in der Datenstruktur entstanden.



### Thematische Ausrichtung und Zielsetzung

Ziel meines Projekts war es, Beiträge aus sozialen Netzwerken wie TikTok, Reddit und YouTube automatisiert zu erfassen, zu bereinigen und hinsichtlich Stimmung, thematischer Einordnung und möglicher Popularität zu analysieren. Dabei sollte nicht nur ein Modell trainiert werden, sondern ein vollständiger, reproduzierbarer Analyseprozess entstehen – von der Datenbeschaffung über das Feature Engineering bis hin zur Deployment-fähigen Architektur.

Der Fokus lag somit auf einem Ende-zu-Ende-Ansatz im Sinne moderner MLOps: Automatisierung, Wiederverwendbarkeit und Modularisierung standen im Vordergrund, ohne dabei die inhaltliche Aussagekraft der Analysen aus dem Blick zu verlieren.


### Datenbeschaffung: Plattformlogik, Instabilität und Vereinheitlichung

Die Datenbeschaffung stellte sich als der technisch wie organisatorisch aufwendigste Teil des Projekts heraus. Die beteiligten Plattformen – Reddit, Instagram, X (ehemals Twitter), TikTok und YouTube – erforderten jeweils eigene Strategien, Scraping-Logik oder die Nutzung (inoffizieller) APIs. Für nahezu jede Quelle waren mehrere Versuche notwendig, bis eine stabile Datengewinnung möglich war.

Ich begann mit Reddit, da hier eine gut dokumentierte und stabile API zur Verfügung steht. Trotz dieser vergleichsweise günstigen Voraussetzungen benötigte ich einige Zeit, um ein robustes Scraping-Skript zu entwickeln, das regelmäßig und zuverlässig Daten erfassen konnte.

Deutlich komplizierter gestaltete sich die Arbeit mit Instagram. Meta stellt keine öffentliche API zur Verfügung, wodurch viele gängige Python-Bibliotheken (z. B. `instaloader`, `instascrape`) schnell an technische oder rechtliche Grenzen stießen. Die einzig halbwegs funktionierende Lösung bestand darin, mit Selenium einen manuellen Nutzerzugriff zu simulieren: Ich legte einen neuen Account an, loggte mich automatisiert ein und sammelte Beiträge über die „Explore“-Seite. Dabei wurden zunächst nur rudimentäre Informationen abgerufen; Details wie Likes, Captions oder Benutzernamen sollten nachträglich über XPath extrahiert werden. Allerdings stellte sich heraus, dass Instagram seine Seitenstruktur häufig ändert, was den Ansatz sehr instabil machte. Aufgrund dieser Unsicherheit entschied ich mich, die Arbeit an Instagram-Daten zunächst zurückzustellen.

Auch beim Versuch, Daten von X (ehemals Twitter) zu extrahieren, war ich nicht erfolgreich. Mehrere Bibliotheken und manuelle Versuche scheiterten – nach weiterer Recherche stellte sich heraus, dass die Schnittstelle nur wenige Tage vor Projektbeginn vollständig abgeschaltet wurde. Damit war auch diese Datenquelle nicht weiter verfolgbar.

TikTok erwies sich als unerwartet zuverlässig, wenn auch nicht problemlos. Nach dem Test mehrerer Bibliotheken fand ich eine inoffizielle API-Lösung, mit der sich Beiträge stabil abrufen ließen – inklusive wichtiger Metriken wie Likes, Shares, Kommentare und Plays.

Zuletzt ergänzte ich YouTube als Datenquelle. Der Zugriff über die offizielle YouTube-API war unkompliziert. Allerdings stellte sich später heraus, dass mein Skript wiederholt dieselben Beiträge von der Explore-Seite erfasste. Anfangs schien der Import erfolgreich („50 Einträge hinzugefügt“), tatsächlich handelte es sich jedoch oft um Duplikate. Auch diese Herausforderung musste nachträglich durch entsprechende Filterung gelöst werden.

#### Automatisierung und Infrastruktur

Ein Ziel war es, das Scraping zu automatisieren, um über längere Zeiträume einen belastbaren Datensatz aufzubauen. Der erste Ansatz – ein dauerhaft laufendes Python-Skript – erwies sich als instabil. Auch die Nutzung des Windows Task Schedulers scheiterte auf meinem Arbeitslaptop, da sicherheitsrelevante Einschränkungen (IBM Security) den geplanten Zugriff blockierten.

Ich versuchte daraufhin, die Infrastruktur vollständig zu deployen – u. a. über Render, Replit und Kubernetes (Minikube, Kind). Doch keine der Lösungen war in der Lage, das TikTok-Scraping zuverlässig auszuführen. Die betreffende API funktionierte ausschließlich lokal. Deshalb entschied ich mich für eine hybride Architektur: Das Backend lief online, das TikTok-Scraping wurde regelmäßig lokal durchgeführt und per API an den Server synchronisiert.

#### Vereinheitlichung der Daten

Die Konsolidierung der Daten aus den verschiedenen Plattformen stellte eine weitere Herausforderung dar. Zwischenzeitlich hatte ich Spaltennamen und Strukturen verändert – teilweise sogar mehrfach. Einige Felder waren plattformspezifisch, andere sollten standardisiert zusammengeführt werden. Dies erforderte nicht nur sorgfältige Mappings, sondern auch eine Normalisierung von Datentypen, Zeitformaten und Bezeichnern. Die Migration von CSV-Dateien in eine relationale SQLite-Datenbank erleichterte diesen Prozess erheblich, erforderte jedoch umfassende Nacharbeiten.



### Arbeiten auf zwei Geräten

Im Verlauf des Projekts arbeitete ich abwechselnd auf zwei Systemen: einem privaten MacBook und einem Windows-basierten Arbeitslaptop. Diese duale Infrastruktur brachte einige technische Herausforderungen mit sich – insbesondere beim Umgang mit Git (z. B. Konflikte durch unterschiedliche Zeilenendungen, Dateipfade oder Python-Umgebungen).

Trotz dieser Reibungspunkte stellte sich die parallele Entwicklung auf beiden Plattformen im Nachhinein als vorteilhaft heraus: Die Anwendung ist inzwischen plattformübergreifend funktionsfähig – sowohl unter macOS als auch unter Windows. Dies erhöht nicht nur die Robustheit des Projekts, sondern schafft zugleich eine größere Einsatzflexibilität im praktischen Umfeld.



###  Architektur & Deployment: Komplexität sichtbar machen

Ein zentrales Ziel dieses Projekts war es, eine produktionsnahe, plattformunabhängige Infrastruktur für automatisierte Machine-Learning-Pipelines zu entwickeln – unter Verzicht auf Docker Desktop. Ich setzte konsequent auf **Podman** zur Containerisierung, orchestrierte alle Schritte mit **ZenML** und integrierte Backend (FastAPI), Frontend (Streamlit), Embedding-Index (Qdrant) und Datenbank (SQLite).

#### Ursprüngliche Architekturidee

Mein ursprünglicher Plan sah den Einsatz von **Kubeflow Pipelines** auf einem lokalen Kubernetes-Cluster vor. Auf meinem macOS-System testete ich:

* **Minikube mit Podman:** Der API-Server (`localhost:8443`) ließ sich nicht starten, Add-ons wie `storage-provisioner` schlugen fehl, `kubectl get nodes` war nicht verfügbar (EOF-Fehler).
* **Kubeflow Deployment:** Zwar ließen sich die YAML-Ressourcen anwenden, doch blieben die Pods im Status `ContainerCreating`. Port-Forwarding und UI-Aufruf scheiterten regelmäßig.

Ein paralleler Test auf Windows mit `kind` brachte ebenfalls keine stabile Umgebung hervor – ein Muster zeichnete sich ab: **Kubeflow ist lokal ohne Docker Desktop nur schwer zuverlässig nutzbar.**

#### Weitere Alternativen und Einschränkungen

* **Render** funktionierte nicht stabil mit Qdrant oder automatisiertem Scraping.
* **Replit** konnte keine zuverlässige SQLite-Verbindung halten.
*  Auch **kind** und **Bare-Metal-Kubernetes** waren nicht mit meinem Podman, SQLite FastAPI Setup praktikabel.
* Die TikTok-Schnittstelle blockierte externe Serveranfragen, weshalb ein lokales Scraping nötig blieb.

#### Letztlich gewählte Lösung

Ich entschied mich für eine **hybride Architektur**:

* Daten werden **lokal gescraped**, insbesondere TikTok.
* Die ML-Pipelines laufen containerisiert und orchestriert mit **ZenML**.
* Das System ist über einen **Cloudflare Tunnel** erreichbar.
* FastAPI dient als Schnittstelle zur API, das Frontend läuft via Streamlit.

Diese pragmatische Lösung ist nicht vollständig cloudbasiert, aber in sich stabil und gut dokumentierbar – und erfüllt damit die Anforderungen an ein prototypisches MLOps-System.



###  Modellierung & Analyse: Von der Theorie zur Anwendung

Die eigentliche Analyse erfolgte in einem separaten ZenML-Notebook mit Fokus auf **Textklassifikation, Zeitreihenanalyse und Sentimentauswertung**. Dabei kamen folgende Verfahren zum Einsatz:

* **BERTopic** zur Topic-Zuordnung über Zeit
* **VADER** und **RoBERTa** zur Sentimentanalyse (regelbasiert + transformerbasiert)
* **TF-IDF & LDA** für klassische thematische Clusterbildung
* **Prophet** zur Prognose der Topic-Entwicklung über Zeit
* **Random Forest & Logistic Regression** zur Popularitätsklassifikation

Das Notebook wurde mehrfach überarbeitet und modularisiert. Fehlerquellen wie fehlerhafte Timestamps (`topics_over_time`) oder Performance-Probleme beim RoBERTa-Batchprocessing wurden gezielt behoben. Neue Visualisierungen (absolute/relative Topic-Anteile, Heatmaps) und Sentiment-Korrelationen runden die explorative Analyse ab.


###  Fazit & Ausblick

**Dieses Projekt war ein Lehrstück in moderner ML-Systementwicklung.** Die Herausforderungen lagen nicht in der Modellierung allein, sondern in der Kombination aus Datenbeschaffung, Stabilität, Plattformunabhängigkeit und Reproduzierbarkeit. Durch die Umstellung auf ZenML, lokale Containerisierung mit Podman und die Entscheidung für eine hybride Architektur wurde ein System realisiert, das modular, erweiterbar und nachvollziehbar ist.

**Wichtige Erkenntnisse:**

* **Deployment ist oft schwieriger als Modelltraining.**
* **Plattformunabhängigkeit ist erreichbar, aber kostet Zeit.**
* **Kubeflow ist mächtig, aber (noch) nicht ideal für lokale Entwickler-Setups ohne Docker Desktop.**
* **ZenML** bietet eine einfache, produktionsnahe Alternative – besonders in frühen Projektphasen.
* **RoBERTa, BERTopic, Prophet** & Co. liefern interessante Einsichten – vorausgesetzt, die Datenbasis ist stabil.

**Nächste Schritte:**

* Aufbau eines stabilen Deployment-Ziels (ggf. ZenML + Cloud)
* Interaktive Visualisierung im Streamlit-Frontend verbessern
* Erweiterung um Live-Monitoring, Feedback-Loop und Model-Feedback durch Nutzer
