# Social Media Trend Analysis - Systemarchitektur

## Überblick

Diese Anwendung bietet eine Benutzeroberfläche zur Analyse von Social-Media-Trends auf verschiedenen Plattformen (Reddit, TikTok, YouTube) mit Fokus auf ML OPS-Funktionalitäten.

## Architekturdiagramm

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Data Sources  │     │  ML Pipeline    │     │   Monitoring    │
│  ┌───────────┐  │     │  ┌───────────┐  │     │  ┌───────────┐  │
│  │  Reddit   │  │     │  │ Data Prep │  │     │  │ Prometheus│  │
│  └───────────┘  │     │  └───────────┘  │     │  └───────────┘  │
│  ┌───────────┐  │     │  ┌───────────┐  │     │  ┌───────────┐  │
│  │  TikTok   │──┼────▶│  │ Model     │──┼────▶│  │ Grafana   │  │
│  └───────────┘  │     │  │ Training  │  │     │  └───────────┘  │
│  ┌───────────┐  │     │  └───────────┘  │     │  ┌───────────┐  │
│  │  YouTube  │  │     │  ┌───────────┐  │     │  │ Logging   │  │
│  └───────────┘  │     │  │ Deployment│  │     │  └───────────┘  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲                      ▲                       ▲
         │                      │                       │
         └──────────────────────┼───────────────────────┘
                                │
                     ┌─────────────────────┐
                     │  ZenML Orchestration│
                     │  ┌───────────────┐  │
                     │  │ Pipeline Mgmt │  │
                     │  └───────────────┘  │
                     │  ┌───────────────┐  │
                     │  │ Model Registry│  │
                     │  └───────────────┘  │
                     └─────────────────────┘
                                ▲
                                │
                     ┌─────────────────────┐
                     │   Frontend (React)  │
                     │  ┌───────────────┐  │
                     │  │ Visualization │  │
                     │  └───────────────┘  │
                     │  ┌───────────────┐  │
                     │  │ Dashboards    │  │
                     │  └───────────────┘  │
                     └─────────────────────┘
```

## Hauptkomponenten

### 1. Datenquellen
- **Reddit**: API-basierte Datensammlung für Reddit-Posts und -Kommentare
- **TikTok**: Erfassung von TikTok-Trends und Video-Metadaten
- **YouTube**: Sammlung von YouTube-Video-Informationen und Trends

### 2. ML Pipeline
- **Datenvorbereitung**: Reinigung, Transformation und Aufbereitung der Daten
- **Modelltraining**: Training von NLP-Modellen für Trend-, Topic- und Sentiment-Analyse
- **Deployment**: Bereitstellung der Modelle für Vorhersagen und Analysen

### 3. Monitoring & Observability
- **Prometheus**: Erfassung von Metriken für Modelle und Infrastruktur
- **Grafana**: Visualisierung der gesammelten Metriken mit anpassbaren Dashboards
- **Logging**: Strukturierte Logs für bessere Nachverfolgbarkeit

### 4. Orchestrierung
- **ZenML**: Management und Orchestrierung der ML-Pipelines
- **Pipeline-Verwaltung**: Scheduling, Ausführung und Überwachung der Pipelines
- **Modell-Registry**: Versionierung und Tracking der trainierten Modelle

### 5. Frontend
- **React-Anwendung**: Single-Page-Application für Benutzerinteraktion
- **Visualisierungen**: Interaktive Charts und Grafiken für Trendanalysen
- **Dashboards**: Anpassbare Ansichten für verschiedene Aspekte der Datenanalyse

## API-Fallback-Mechanismus

Die Anwendung verwendet einen intelligenten Fallback-Mechanismus:

1. Primär werden Daten von der echten API abgefragt
2. Bei Nichtverfügbarkeit der API wird automatisch auf Mock-Daten umgeschaltet
3. Konsistente Datenstrukturen ermöglichen nahtlosen Übergang zwischen echten und Mock-Daten

## MLOps-Technologie-Stack

- **Frontend**: React, Chart.js, Bootstrap
- **Backend**: Python, FastAPI, Flask
- **Datenbank**: PostgreSQL
- **ML-Tools**: ZenML, scikit-learn, NLTK, HuggingFace Transformers
- **Monitoring**: Prometheus, Grafana
- **Deployment**: Docker, Vercel (Frontend), Railway (Backend)

## Repository

Der Quellcode ist verfügbar auf GitHub: [TrendAnalyseSocialMedia](https://github.com/SofiePischl/TrendAnalyseSocialMedia) 