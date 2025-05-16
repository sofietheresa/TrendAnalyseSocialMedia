# 📈 TrendAnalyseSocialMedia

Eine moderne Webanwendung zur Analyse von Social Media Trends auf TikTok, YouTube und Reddit.

## 🚀 Features

- 🔍 Automatisches **Scraping** von TikTok, YouTube und Reddit
- 📊 **Interaktives Dashboard** zur Visualisierung der Trends
- 📅 **Tägliche Statistiken** über gesammelte Inhalte
- 🔄 **Scheduler** für regelmäßige Datenerfassung
- 📱 **Responsives Frontend** für Desktop und Mobile
- 🗄️ **PostgreSQL Datenbank** für strukturierte Datenspeicherung
- ☁️ **Railway Deployment** für einfache Cloud-Bereitstellung
- 🤖 **ML-Pipeline** zur automatisierten Analyse von Trends
- 📖 **Dokumentationsbereich** mit Präsentationsviewer

## 📦 Projektstruktur

```
├── src/                  # Backend-Code
│   ├── api/              # API-Endpunkte & Dienste
│   ├── scheduler/        # Scheduler-Komponenten
│   │   ├── jobs/         # Individuelle Scraper
│   │   │   ├── reddit_scraper.py
│   │   │   ├── tiktok_scraper.py
│   │   │   └── youtube_scraper.py
│   │   └── main_scraper.py  # Hauptscheduler
│   ├── pipelines/        # ML-Pipeline Komponenten
│   │   ├── steps/        # Pipeline-Schritte
│   │   └── mlops_pipeline.py
│   ├── main.py           # FastAPI Hauptanwendung
│   ├── db_connection.py  # Datenbankverbindung
│   └── models.py         # Datenmodelle
├── app/                  # Railway-Deployment
│   ├── main.py           # API Anwendung
│   ├── railway.py        # Railway Starter
│   └── run_railway.sh    # Start-Skript
├── frontend/             # React Frontend
│   ├── src/              # Frontend-Quellcode
│   │   ├── components/   # React-Komponenten
│   │   ├── services/     # API-Dienste
│   │   └── App.js        # Hauptkomponente
│   └── package.json      # NPM-Konfiguration
├── notebooks/            # Jupyter Notebooks für Analyse & Entwicklung
├── notebooks_explained/  # Detaillierte Notebooks mit Erklärungen
├── docs/                 # Dokumentation & Präsentationen
│   └── presentation_images/  # Bilder für Präsentationsviewer
├── requirements.txt      # Python-Abhängigkeiten
├── Procfile              # Railway-Konfiguration
└── railway.toml          # Railway-Deployment-Konfiguration
```

## 🛠️ Installation

### Voraussetzungen

- Python 3.11+
- Node.js 16+ (für das React-Frontend)
- PostgreSQL-Datenbank

### 1. Repository klonen

```bash
git clone https://github.com/yourusername/TrendAnalyseSocialMedia.git
cd TrendAnalyseSocialMedia
```

### 2. Python-Abhängigkeiten installieren

```bash
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Umgebungsvariablen einrichten

Erstellen Sie eine `.env` Datei im Hauptverzeichnis:

```env
DATABASE_URL=postgresql://username:password@host:port/dbname
REDDIT_ID=your_reddit_client_id
REDDIT_SECRET=your_reddit_client_secret
YT_KEY=your_youtube_api_key
MS_TOKEN=your_tiktok_ms_token
```

### 4. Frontend-Abhängigkeiten installieren

```bash
cd frontend
npm install
```

## 🚀 Anwendung starten

### Backend lokal ausführen

```bash
# API starten
make start

# Oder direkt:
uvicorn src.main:app --reload
```

### Scraper ausführen

```bash
# Alle Scraper einmalig ausführen
make run-scrapers

# Oder einzeln:
make run-reddit
make run-tiktok
make run-youtube

# Scheduler für periodisches Scraping starten
make run-scheduler
```

### Frontend starten

```bash
make start-frontend

# Oder direkt:
cd frontend && npm start
```

## 📊 Frontend-Komponenten

Die Anwendung besteht aus mehreren Hauptseiten:

1. **Dashboard** - Zeigt Statistiken und Trends an
   - Tägliche Post-Anzahl pro Plattform
   - Scraper-Status (aktiv/inaktiv)
   - Gesamtstatistiken

2. **Daten-Ansicht** - Zeigt die neuesten Inhalte pro Plattform
   - Filterung nach Plattform (Reddit, TikTok, YouTube)
   - Einstellbare Anzahl an angezeigten Einträgen
   - Sortierung nach Datum (neueste zuerst)

3. **Pipeline-Verwaltung** - Verwaltung der ML-Pipeline
   - Status der Pipelines
   - Ausführung und Überwachung
   - Ergebnisanzeige

4. **Dokumentation** - Projektdokumentation und Präsentationen
   - Interaktiver Präsentationsviewer
   - Analysedaten
   - System-Logs

## 🧠 ML-Pipeline

Die Anwendung enthält eine automatisierte ML-Pipeline mit folgenden Schritten:

1. **Datensammlung** - Automatisches Scraping aus verschiedenen Quellen
2. **Vorverarbeitung** - Textbereinigung und Feature-Extraktion
3. **Datenexploration** - Statistische Analyse der gesammelten Daten
4. **Vorhersagen** - Trendanalysen und Mustererkennungen

Die Pipeline ist modular aufgebaut und kann durch weitere Komponenten erweitert werden.

## 🔄 Deployment

Die Anwendung ist für das Deployment auf Railway konfiguriert:

```bash
# Railway-Deployment
railway up
```

Die Konfiguration ist in `railway.toml` und `Procfile` definiert.

## 🧪 Entwicklung

Für die Entwicklung stehen Makefile-Befehle zur Verfügung:

```bash
# Typische Entwicklungsbefehle
make install            # Abhängigkeiten installieren
make clean              # Temporäre Dateien aufräumen
make test               # Tests ausführen
make lint               # Code-Qualitätsprüfung
```

## 📝 Dokumentation

Die ausführliche Dokumentation ist im Frontend unter `/documentation` verfügbar. Sie enthält:

- Detaillierte Erklärungen zu allen Komponenten
- Interaktiven Präsentationsviewer
- API-Dokumentation
- System-Logs und Status

## 📄 Lizenz

Dieses Projekt ist lizenziert unter der MIT-Lizenz.

## Running the Application

### Backend Service

The application uses a single backend API for all endpoints:

```bash
# Start the backend API
python src/main.py
```

### Frontend

The frontend requires the following environment variable:

- `REACT_APP_API_URL`: URL of the API (default: http://localhost:8000)

To run the frontend:

```bash
cd frontend
npm install
npm start
```

## Deployment

Deploy the application to Railway using:

```bash
railway up
```

After deployment, update your frontend environment variable with the deployed URL.

## Backend API Endpoints

Key API endpoints:

- `/api/mlops/models/{model_name}/drift` - Get model drift metrics
- `/api/mlops/pipelines` - Get all pipelines
- `/api/mlops/pipelines/{pipeline_id}` - Get specific pipeline
- `/api/mlops/pipelines/{pipeline_id}/executions` - Get pipeline executions
- `/api/mlops/pipelines/{pipeline_id}/execute` - Execute a pipeline
