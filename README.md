# Social Media Trend Analysis

Eine moderne Anwendung zur Analyse von Social Media Trends mit einer Web-Oberfläche und Echtzeit-Monitoring.

## Features

- **Daten-Scraping** von verschiedenen Social Media Plattformen:
  - TikTok
  - YouTube
  - Reddit
- **Automatische Analyse** von Trends und Mustern
- **Web-Dashboard** zur Visualisierung der Ergebnisse
- **Echtzeit-Monitoring** der Pipeline-Performance
- **REST-API** für externe Integrationen

## Technologie-Stack

- **Backend:**

  - Python 3.11+
  - FastAPI
  - ZenML für ML-Pipelines
  - TensorFlow für ML-Modelle
  - NLTK für Textverarbeitung

- **Frontend:**

  - React
  - Chart.js für Visualisierungen
  - Modernes, responsives Design

- **Infrastruktur:**
  - Docker & Docker Compose
  - Nginx als Reverse Proxy
  - Prometheus & Grafana für Monitoring
  - Qdrant für Vektordatenbank

## Installation

1. **Voraussetzungen:**

   ```bash
   - Docker & Docker Compose
   - Python 3.11+
   - Node.js 16+ (für Frontend-Entwicklung)
   ```

2. **Repository klonen:**

   ```bash
   git clone https://github.com/yourusername/trend-analyse-social-media.git
   cd trend-analyse-social-media
   ```

3. **Python-Paket installieren:**

   ```bash
   pip install -e .
   ```

4. **Umgebungsvariablen konfigurieren:**

   ```bash
   cp .env.example .env
   # Bearbeite .env mit deinen API-Keys und Konfigurationen
   ```

5. **Docker-Container starten:**
   ```bash
   docker-compose up -d
   ```

## Verwendung

### Web-Dashboard

- Öffne `https://deine-domain.de` im Browser
- Dashboard zeigt aktuelle Trends und Analysen
- Pipeline kann manuell gestartet werden
- Echtzeit-Updates alle 30 Sekunden

### API-Endpunkte

- `GET /api/` - API-Dokumentation
- `POST /api/run-pipeline` - Pipeline starten
- `GET /api/status` - Status der letzten Analyse
- `GET /api/metrics` - Prometheus Metriken

### Monitoring

- Grafana Dashboard: `https://deine-domain.de:3001`
  - Login: admin/admin
  - Pipeline-Performance
  - Fehlerraten
  - Ressourcennutzung

## Projektstruktur

```
trend-analyse-social-media/
├── src/                    # Hauptquellcode
│   ├── api.py             # FastAPI-Anwendung
│   ├── pipelines/         # ML-Pipelines
│   └── scrapers/          # Social Media Scraper
├── frontend/              # React Frontend
├── docker-compose.yml     # Docker-Konfiguration
├── Dockerfile            # Docker-Build
├── nginx.conf            # Nginx-Konfiguration
├── setup.py              # Python-Paket-Konfiguration
└── setup_ssl.sh          # SSL-Setup-Skript
```

## Entwicklung

### Frontend-Entwicklung

```bash
cd frontend
npm install
npm start
```

### Backend-Entwicklung

```bash
# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # oder `venv\Scripts\activate` unter Windows

# Abhängigkeiten installieren
pip install -e .
```

### Tests ausführen

```bash
python -m pytest tests/
```

## Deployment

1. **SSL-Zertifikate einrichten:**

   ```bash
   chmod +x setup_ssl.sh
   ./setup_ssl.sh deine-domain.de
   ```

2. **Nginx-Konfiguration anpassen:**

   - Bearbeite `nginx.conf`
   - Ersetze `server_name _;` mit deiner Domain

3. **Container neu starten:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Monitoring & Wartung

- **Logs anzeigen:**

  ```bash
  docker-compose logs -f
  ```

- **Container-Status prüfen:**

  ```bash
  docker-compose ps
  ```

- **Backup erstellen:**
  ```bash
  # Daten sichern
  tar -czf backup.tar.gz data/ qdrant_storage/
  ```

## Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

## Beitragen

1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Committe deine Änderungen
4. Push zum Branch
5. Erstelle einen Pull Request

## Kontakt

Bei Fragen oder Problemen, erstelle bitte ein Issue im GitHub-Repository.
