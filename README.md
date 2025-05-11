Hier ist eine überarbeitete Version der README-Datei inklusive Architekturgrafik, die du direkt einbinden kannst:

---

# 📈 Social Media Trend Analysis

Ein modernes Analyseframework für aktuelle Trends auf TikTok, YouTube und Reddit – mit MLOps, Dashboard, Scheduler & Vektor-DB.

## 🚀 Features

- 🛰️ **Daten-Ingestion** von TikTok, YouTube & Reddit
- 🤖 **ML-Pipeline mit ZenML**: Sentiment & Trendanalyse
- 📊 **Interaktive Dashboards** via Streamlit
- 🧠 **Vektorspeicherung** in Qdrant + semantische Suche
- 🗃️ **SQLite** für strukturierte Rohdaten
- 🔁 **Scheduler + Orchestration** via ZenML
- 📡 **Monitoring** mit Prometheus & Grafana
- 🔗 **REST-API** (FastAPI) für Externe Dienste

## 🧩 Architektur

![Architektur](./docs/architecture.png)

> **Hinweis:** Die Architektur zeigt den Datenfluss vom Scraping bis zur Vektor-Datenbank.

## ⚙️ Tech Stack

**Backend:**

- Python 3.11, FastAPI, ZenML, NLTK, TensorFlow
- SQLite, Qdrant

**Frontend:**

- Streamlit

**Orchestration & Container:**

- ZenML Pipelines
- Podman statt Docker
- Optional: Docker Compose / systemd

**Monitoring:**

- Prometheus + Grafana

---

## 🛠️ Installation

### Voraussetzungen

- Python 3.11+
- Node.js 16+ (nur bei React-Frontend)
- Podman (alternativ: Docker)
- Optional: `make`, `poetry`, `zenml`

### 1. Repository klonen

```bash
git clone https://github.com/yourname/trend-analyse-social-media.git
cd trend-analyse-social-media
```

### 2. Python-Abhängigkeiten installieren

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Umgebungsvariablen anlegen

```bash
cp .env.example .env
# API-Keys und Pfade eintragen
```

---

## 📦 Verwendung

### Web-Dashboard (Streamlit)

```bash
make streamlit
```

Zeigt:

- Linecharts (Postanzahl über Zeit)
- Seiten für Reddit, TikTok, YouTube
- Orchestrator-Seite mit ZenML Stack-Infos & Triggern

### FastAPI starten

```bash
make start-api
```

**API-Endpunkte:**

- `GET /api/docs`
- `POST /api/run-pipeline`
- `GET /api/status`

---

## 🧪 Pipelines & ZenML

- Starte Pipelines über UI oder CLI (`zenml run`)
- Nutze `zenml describe` zur Analyse des Stacks
- Vektor-Embeddings landen in Qdrant

---

## 📈 Monitoring mit Grafana

1. Prometheus über `docker-compose` starten
2. Grafana öffnen unter `http://localhost:3000`
3. Login: admin/admin
4. Dashboard für Metriken wie:

   - Pipeline-Durchläufe
   - Fehlerraten
   - Latenz / Dauer
   - Speicherlast

---

## 📁 Projektstruktur

```bash
├── src/
│   ├── steps/               # ZenML Steps
│   ├── scheduler/           # Zeitgesteuerte Tasks
│   ├── api/                 # FastAPI App
├── frontend/
│   ├── app.py               # Streamlit-Frontend
│   ├── public/              # Optional: React UI
├── notebooks/               # Explorative Analyse
├── qdrant_storage/          # Vektor-DB
├── data/                    # SQLite-Datenbank
├── logs/                    # Logdateien
├── Dockerfile               # Build-Spezifikation
└── zenml_pipeline.py        # Haupt-Pipeline
```

---

## 🔐 Sicherheit & Produktion

- Nutze `Podman` mit Rootless-Containern
- Setze Nginx reverse proxy mit TLS ein
- Verwende `.env` für Secrets (nicht committen!)
- Monitoring via Grafana & Prometheus
- Backups per `tar czf backup.tar.gz data/ qdrant_storage/`
