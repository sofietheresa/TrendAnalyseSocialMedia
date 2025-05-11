Danke für die Ergänzungen. Auf dieser Grundlage habe ich den Erfahrungsbericht nun etwas förmlicher, kohärenter und trotzdem persönlich gehalten. Er ist gut geeignet für eine Projektdokumentation oder einen schriftlichen Anhang im Rahmen einer Abgabe:

---

## 📘 Erfahrungsbericht zum Projekt: Social-Media-Datenanalyse mit MLOps-Integration

### Einleitung

Mein Projekt startete offiziell am 11. April 2025 – also vor exakt 30 Tagen. Der Einstieg gestaltete sich jedoch schwieriger als erwartet, da ich zunächst mit einem anderen Thema begonnen hatte. Erst nach mehreren Umorientierungen und viel Unsicherheit entschied ich mich für die Analyse von Social-Media-Daten – mit dem Schwerpunkt auf automatisierter Datengewinnung, Vorverarbeitung und maschinellem Lernen innerhalb einer produktionsreifen MLOps-Architektur.

Die vergangenen zehn Tage waren besonders intensiv. Mit wachsendem Zeitdruck konnte ich in kurzer Zeit große Fortschritte erzielen, auch wenn viele Hürden auf dem Weg lagen. Zwischenzeitlich war ich verzweifelt, doch am Ende steht ein funktionierendes System – mit Optimierungspotenzial, aber klarer Struktur und ausbaufähiger Funktionalität.

---

### Thematische Ausrichtung und Zielsetzung

Ziel meines Projekts war es, Beiträge aus sozialen Netzwerken wie Instagram, TikTok und Reddit automatisiert zu erfassen und hinsichtlich Stimmung, Themen und potenzieller Relevanz zu analysieren. Ich wollte herausfinden, wie sich Inhalte typisieren und Stimmungen in Texten quantifizieren lassen – und gleichzeitig herausfordernde Aspekte wie Datenzugriff, Deployment und Wiederholbarkeit sauber lösen.

---

### Datenbeschaffung: Vom Experiment zur Infrastruktur

Der wohl aufwendigste und nervenaufreibendste Teil des Projekts war das Webscraping. Ich hatte zunächst vor, Instagram und die Plattform X (ehemals Twitter) gemeinsam zu verarbeiten, musste jedoch aufgrund unzuverlässiger Schnittstellen und technischer Einschränkungen letztere streichen.

Für Instagram nutzte ich verschiedene Python-Bibliotheken, darunter `instaloader`, `instascrape` und `instagram-scraper`, stieß jedoch schnell an deren Grenzen (Rate-Limits, fehlender Login-Support, etc.). Die letztlich funktionierende Lösung war ein automatisierter Browserzugriff mittels Selenium – technisch aufwendig, aber zuverlässig genug für ein erstes Datenkorpus.

Ich legte früh fest, welche Informationen ich speichern wollte – darunter URL, Veröffentlichungsdatum, ALT-Text, Benutzername, Bildunterschrift und (wenn möglich) die Anzahl der Likes. Die Datenstruktur wurde mehrfach angepasst und erst spät in eine relationale Datenbank überführt. Bis dahin arbeitete ich ausschließlich mit CSV-Dateien, was bei paralleler Entwicklung und Versionskontrolle zu zahlreichen Merge-Konflikten führte.

---

### Architektur & Deployment: Container, Scheduler und hybride Systeme

Ein zentrales Ziel war es, das Projekt modular und containerisiert umzusetzen. Ich setzte konsequent auf Docker, um alle Komponenten sauber zu kapseln. Für das Hosting und Scheduling verwendete ich Render sowie GitHub Actions. Doch auch hier traten unerwartete Probleme auf: TikTok ließ sich innerhalb des Containers nicht zuverlässig scrapen, weshalb ich auf eine hybride Lösung mit meinem lokalen Rechner als Datenerfassungseinheit ausweichen musste.

Render stellte sich zudem als ressourcenintensiv heraus – das Starten der App dauerte ungewöhnlich lange. Auch das Scheduling über den Windows Task Scheduler scheiterte, u. a. an Sicherheitsrichtlinien des Betriebssystems (Stichwort: IBM Security). Trotz alledem gelang es mir, eine funktionierende Architektur zu etablieren, in der Daten gesammelt, verarbeitet und ausgewertet werden konnten.

---

### Modellierung & Analyse: Zwischen Experiment und Pipeline

Die eigentliche Modellierung rückte lange in den Hintergrund. Erst als die Datenbeschaffung weitgehend funktionierte, begann ich mit der Umsetzung von Analyse- und Vorhersagemodellen. Zum Einsatz kamen:

- **Feature-Engineering** mit TF-IDF
- **Regression** über Random Forest zur Bewertung von Popularität
- **Topic Modeling** mittels LDA und BERTopic
- **Sentimentanalyse** mit TextBlob, VADER und einem Transformer-Modell

Zur Evaluation nutzte ich Metriken wie MSE, MAE, R², Explained Variance und weitere. Die Vorhersagen selbst sind aktuell noch wenig aussagekräftig, was ich auf die Heterogenität und begrenzte Größe der Datensätze zurückführe. Hier besteht noch Optimierungsbedarf.

Die gesamte Modellpipeline wurde mit **ZenML** orchestriert. Ich definierte sowohl Preprocessing- als auch Training- und Inferenzschritte in wiederverwendbaren Pipelines. Für Visualisierung und Interaktion baute ich ein **Streamlit-Dashboard**, über das sich unter anderem die Pipelines starten lassen.

---

### Reflexion & Ausblick

Dieses Projekt war für mich ein Wechselbad der Gefühle. Über Wochen hinweg kämpfte ich mit instabilen Schnittstellen, fehlerhaften Abhängigkeiten, Deployment-Problemen und einer steilen Lernkurve im Bereich MLOps. Die letzten zehn Tage waren geprägt von hoher Intensität, aber auch von einer klaren Struktur und sichtbaren Fortschritten.

Die wichtigsten Learnings:

- **Scraping ist nie trivial**, insbesondere bei Plattformen ohne stabile öffentliche APIs.
- **Containerisierung hilft**, aber bringt auch neue Herausforderungen.
- **MLOps ist mehr als Deployment** – es beginnt mit Datenverfügbarkeit, Monitoring, Automatisierung und endet erst bei nachvollziehbarer Evaluation.
- **Alleine arbeiten heißt alles selbst entscheiden müssen** – das ist einerseits befreiend, andererseits fordernd.

Für die verbleibende Projektzeit plane ich, die Modellgüte zu verbessern, das Dashboard interaktiver zu gestalten und den Übergang von Entwicklung zu Betrieb noch klarer zu strukturieren.
