## Erfahrungsbericht zum Projekt: Social-Media-Datenanalyse mit MLOps-Integration

### Einleitung

Mein Projekt begann offiziell am 13. März 2025. Der Einstieg gestaltete sich herausfordernd: Ich war zunächst unentschlossen, welches Thema ich verfolgen sollte. Wichtig war mir, ein Vorhaben zu wählen, das sowohl persönliches Interesse weckt als auch gesellschaftliche Relevanz besitzt – abseits gängiger Standardprojekte.

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

* Das Scraping lief zu diesem Zeitpunkt lokal bereits stabil. Nach dem Deployment auf Render zeigte sich jedoch, dass der TikTok-Scraper dort nicht mehr funktionierte – vermutlich wegen der Architektur der inoffiziellen API. Daher entschied ich mich für eine hybride Lösung mit lokalem Scraper und serverseitiger Verarbeitung.

Diese Übersicht verdeutlicht, wie stark der Erfolg des Projekts von einer stabilen Datenbasis abhing – und wie viel Zeit für deren Aufbau erforderlich war. Die kontinuierliche Anpassung des Scraping-Prozesses war dabei die größte Herausforderung.

### Thematische Ausrichtung und Zielsetzung

Ziel meines Projekts war es, Beiträge aus sozialen Netzwerken wie TikTok, Reddit und YouTube automatisiert zu erfassen, zu bereinigen und hinsichtlich Stimmung, thematischer Einordnung und möglicher Popularität zu analysieren. Dabei sollte nicht nur ein Modell trainiert werden, sondern ein vollständiger, reproduzierbarer Analyseprozess entstehen – von der Datenbeschaffung über das Feature Engineering bis hin zur deployment-fähigen Architektur.

Der Fokus lag somit auf einem Ende-zu-Ende-Ansatz im Sinne moderner MLOps: Automatisierung, Wiederverwendbarkeit und Modularisierung standen im Vordergrund, ohne dabei die inhaltliche Aussagekraft der Analysen aus dem Blick zu verlieren.

### Datenbeschaffung: Plattformlogik, Instabilität und Vereinheitlichung

Die Datenbeschaffung war der technisch wie organisatorisch aufwendigste Teil des Projekts. Die beteiligten Plattformen – Reddit, Instagram, X (ehemals Twitter), TikTok und YouTube – erforderten jeweils eigene Strategien, Scraping-Logik oder (inoffizielle) APIs.

Reddit war der Einstiegspunkt – mit stabiler API und gut dokumentierter Struktur. Instagram hingegen war komplex: Meta bietet keine öffentliche API an, was zu wiederholten Problemen mit Selenium-basierten Ansätzen führte. Aufgrund der Instabilität legte ich Instagram vorerst auf Eis.

Auch X (vormals Twitter) fiel aus dem Projekt, da kurz vor Projektbeginn die Schnittstelle abgeschaltet wurde. TikTok hingegen erwies sich als überraschend stabil – mit einer funktionierenden inoffiziellen API. YouTube war über die offizielle API gut anbindbar, allerdings wurden dort häufig Duplikate erfasst, was Filtermechanismen notwendig machte.

### Automatisierung und Infrastruktur

Ein Ziel war die Automatisierung des Datenimports. Ein dauerhaft laufendes Python-Skript war instabil. Weder Windows Task Scheduler noch Replit oder Render erwiesen sich als zuverlässig – insbesondere, da TikTok-Anfragen nur lokal funktionierten.

Ich testete verschiedene Kubernetes-Varianten (Minikube, Kind), scheiterte aber an Kompatibilitätsproblemen mit Podman. Auch ein Deployment über Render funktionierte nicht stabil.

Die finale Lösung: Eine **hybride Architektur**, bei der das Scraping lokal erfolgt und per API an ein Online-Backend übertragen wird. Dieses lief containerisiert mit **ZenML**, **FastAPI**, **SQLite/Qdrant** und einem über **Cloudflare Tunnel** erreichbaren Endpoint.

### Deployment über Railway & Vercel

Nach dem letzten Meeting am 14. Mai habe ich das System auf **Railway** deployed. Anfangs scheiterte das Vorhaben an der zu großen Docker-Image-Größe sowie fehlerhaften Health Checks. Nach Optimierungen lief das Backend stabil, und die Daten wurden in eine **PostgreSQL-Datenbank** auf Railway migriert.

Das Frontend (Streamlit) wurde über **Vercel** bereitgestellt. Auch hier kam es zu wiederholten Darstellungsproblemen, insbesondere durch fehlerhafte API-Verbindungen. Nach mehreren Debugging-Schritten funktioniert das Gesamtsystem nun stabil und öffentlich erreichbar.

### Modellierung & Analyse

Die Analyse erfolgte mit folgenden Methoden:

* **BERTopic** zur Topic-Zuordnung
* **VADER & RoBERTa** für Sentimentanalyse
* **TF-IDF & LDA** zur thematischen Clusterbildung
* **Prophet** zur zeitlichen Trendprognose
* **Random Forest & Logistic Regression** zur Popularitätsklassifikation

Fehlerquellen wie unvollständige Timestamps oder zu große Batch-Größen wurden beseitigt. Die Visualisierungen wurden verbessert und erweitert.

### Arbeiten auf zwei Systemen

Ich arbeitete abwechselnd auf einem MacBook (privat) und einem Windows-Gerät (dienstlich). Dies brachte Herausforderungen bei Git, Dateipfaden und Python-Umgebungen mit sich. Zugleich führte es dazu, dass die Anwendung plattformunabhängig einsetzbar wurde.

### Fazit & Ausblick

Dieses Projekt war ein intensives Lehrstück moderner Machine-Learning-Infrastruktur. Die Hauptprobleme lagen für mich nicht in der Modellierung, sondern in der stabilen, plattformunabhängigen Datenverarbeitung und Automatisierung.

#### Wichtige Learnings

* Deployment ist oft schwieriger als Modelltraining
* Plattformunabhängigkeit ist erreichbar, aber aufwendig
* Kubeflow ist lokal ohne Docker Desktop schwer einsetzbar
* ZenML ist eine gute, leichtgewichtige Alternative
* Stabile Datenbasis ist entscheidend für Modellqualität

#### Weiterer Verbesserungsbedarf

*  **Effizienteres Data Processing**: Nur neue, noch nicht verarbeitete Daten erneut analysieren
*  **Konsistente Datensammlung**: Vollautomatisierung aller Quellen
*  **Weitere Plattformen anbinden**: Instagram & X erneut prüfen
*  *Topic- & Sentiment-Modelle verbessern**
*  **Suchfunktion für Inhalte**: Indexierung & UI-Integration
*  **Nutzungsbasierte Gewichtung**: Stärkere Gewichtung häufig genutzter Plattformen
*  **Plattformspezifische Analysen**: Eigene Modelle für TikTok, YouTube etc.
*  **Frontend mit Parametern erweiterbar**: Interaktive Modellsteuerung durch Nutzende
