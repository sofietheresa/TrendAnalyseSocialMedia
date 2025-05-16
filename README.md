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

## 📦 Projektstruktur

```
├── src/                  # Backend-Code
│   ├── scheduler/        # Scheduler-Komponenten
│   │   ├── jobs/         # Individuelle Scraper
│   │   │   ├── reddit_scraper.py
│   │   │   ├── tiktok_scraper.py
│   │   │   └── youtube_scraper.py
│   │   └── main_scraper.py  # Hauptscheduler
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

Die Anwendung besteht aus zwei Hauptseiten:

1. **Dashboard** - Zeigt Statistiken und Trends an
   - Tägliche Post-Anzahl pro Plattform
   - Scraper-Status (aktiv/inaktiv)
   - Gesamtstatistiken

2. **Daten-Ansicht** - Zeigt die neuesten Inhalte pro Plattform
   - Filterung nach Plattform (Reddit, TikTok, YouTube)
   - Einstellbare Anzahl an angezeigten Einträgen
   - Sortierung nach Datum (neueste zuerst)

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
```

## 📄 Lizenz

Dieses Projekt ist lizenziert unter der MIT-Lizenz.

## Running the Application

### Backend Services

The application consists of two backend services:

1. **Main Backend**: Handles most API requests
2. **Drift API**: A dedicated API for model drift metrics and ML pipeline operations

To run both services:

```bash
# Start the main backend
python src/main.py

# Start the drift API (in a separate terminal)
python drift_api.py
```

### Frontend

The frontend requires the following environment variables:

- `REACT_APP_API_URL`: URL of the main backend API (default: http://localhost:8000)
- `REACT_APP_DRIFT_API_URL`: URL of the drift API (default: http://localhost:8081)

To run the frontend:

```bash
cd frontend
npm install
npm start
```

## Deployment

Both backend services need to be deployed separately. Use the included `deploy.ps1` script to deploy to Railway:

```bash
./deploy.ps1
```

After deployment, update your frontend environment variables with the deployed URLs.
