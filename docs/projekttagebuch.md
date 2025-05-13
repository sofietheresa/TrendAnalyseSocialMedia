## 📘 Erfahrungsbericht zum Projekt: Social-Media-Datenanalyse mit MLOps-Integration

### Einleitung

Mein Projekt startete offiziell am 11. April 2025. Der Einstieg war nicht leicht: Ich war zunächst unentrschlossen, welches Thema ich bearbeiten sollte. Ich wollte gerne ein Thema bearbeiten, das mich selbst interessiert, das kein "Standard Projekt" ist und das auch allgemeine Relevanz hat. So bin ich erstmal auf das das Thema "Analyse von Symptomen im Bereich von Neurodivergenzen" auseinandersetzen.

Hier wäre jedoch die Datenlage schwerig gewesen, sodass ich mich nochmal umorientieren musste. In Zusammenarbeit mit Prof. Dr. Klotz bin ich dann auf das Thema Social Media Trendanalyse gekommen.  

Nachdem das geklärt war, konnte ich anfangen an dem Projekt zu arbeiten. Jedoch war bis hierher schon einiges an Zeit verloren gegangen, nachfolgend eine zeitliche Zusammenfassung:

Zeitübersicht: 


Die vergangenen zehn Tage waren besonders arbeitsintensiv: Mit steigendem Zeitdruck gelang es mir dennoch, ein funktionierendes System aufzubauen – modular, nachvollziehbar und bereit zur Erweiterung, wenn auch mit erkennbarem Optimierungspotenzial.

---

### Thematische Ausrichtung und Zielsetzung

Ziel war es, Beiträge aus sozialen Netzwerken wie TikTok, Reddit und YouTube automatisiert zu erfassen, zu bereinigen und hinsichtlich Stimmung, Themen und potenzieller Relevanz zu analysieren. Dabei ging es nicht nur um reine Modellierung, sondern auch um robuste Datenverarbeitung, Reproduzierbarkeit und Deployment – also eine Ende-zu-Ende-Perspektive auf maschinelles Lernen.

---

### Datenbeschaffung: Vom Rohtext zum Datensatz

Die Datenbeschaffung war der technisch wie organisatorisch aufwendigste Teil des Projekts. Unterschiedliche Plattformen erforderten jeweils eigene Scraping-Logik, API-Nutzung oder Workarounds. Besonders TikTok und Instagram stellten sich als instabil oder schwer zugänglich heraus. Zudem mussten für jede Quelle geeignete Felder, Zeitformate und Identifier definiert werden – was aufgrund der Heterogenität der Plattformen zeitaufwendig war.

Das Zusammenführen der Daten war ebenfalls herausfordernd: Viele Datensätze kamen zunächst als CSV-Dateien mit abweichenden Strukturen. Die Vereinheitlichung und der spätere Import in eine relationale SQLite-Datenbank erforderte sorgfältiges Mapping und wiederholte Umstrukturierung.

---

### Arbeiten auf zwei Geräten

Während der Entwicklung nutzte ich sowohl meinen privaten Mac als auch ein Windows-basiertes Arbeitsgerät. Diese duale Infrastruktur führte zu wiederholten Problemen bei Git (Konflikte durch Zeilenenden, Pfade, Umgebungen), brachte aber auch einen entscheidenden Vorteil: Die Anwendung ist inzwischen sowohl unter macOS als auch unter Windows stabil lauffähig – was zur Plattformunabhängigkeit und Robustheit beiträgt.

---

### Architektur & Deployment: Komplexität sichtbar machen

Ein zentrales Ziel war der produktionsnahe Aufbau der Infrastruktur. Ich setzte konsequent auf Containerisierung (Podman statt Docker) und orchestrierte die Pipelines mit ZenML. Die Anwendung bestand aus mehreren Komponenten: Scraper, Datenbank, Embedding-Index (Qdrant), ML-Pipeline, FastAPI-Backend und Streamlit-Frontend.

Die größte Hürde war jedoch das Deployment. Render funktionierte nicht zuverlässig mit Qdrant, Replit konnte keine SQLite-Verbindungen stabil halten, und auch Versuche mit `minikube`, `kind` oder Bare-Metal-Kubernetes erwiesen sich als zu instabil oder komplex für die verbleibende Zeit. Am Ende fiel die Entscheidung auf eine Cloudflare-Tunnel-Lösung in Verbindung mit lokalem Hosting – eine praktikable, wenn auch nicht finale Lösung.

---

### Modellierung & Analyse

Die Modellierung erfolgte in einem iterativen Prozess. Zur Anwendung kamen:

* **Feature Engineering** (z. B. Textlänge, Hashtag-Zahl, Sentimentwerte)
* **Topic Modeling** (LDA, BERTopic)
* **Sentimentanalyse** (TextBlob, VADER, DistilBERT)
* **Popularitätsregression** (Random Forest)

Alle Modelle wurden in ZenML-Pipelines eingebunden, automatisiert trainiert und evaluiert. Für Visualisierung und Interaktion baute ich ein Streamlit-Dashboard, über das u. a. Vorhersagen und Trends abgerufen werden können.

---

### Reflexion & Ausblick

Dieses Projekt war lehrreich, fordernd und an vielen Stellen frustrierend – aber ebenso befriedigend. Besonders die Kombination aus MLOps, Webscraping, Modellierung und UI-Design war komplex. Dennoch ist es gelungen, ein funktionierendes, nachvollziehbares und erweiterbares System zu bauen.

**Wichtige Erkenntnisse:**

* Plattformdaten sind schwer standardisierbar – Scraping ist fehleranfällig.
* Git und Remote-Work auf mehreren Geräten müssen gut koordiniert werden.
* Deployment ist oft der limitierende Faktor, nicht das Modell.
* Automatisierung (Pipelines, CI, Logging) schafft langfristige Stabilität.

Für die Zukunft plane ich, die Deployment-Strategie weiter zu verbessern, das Frontend interaktiver zu gestalten und mehr echte Nutzerinteraktion in die Modellbewertung einfließen zu lassen.

