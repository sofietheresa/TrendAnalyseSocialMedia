# API-Integrationsplan

## Aktuelle Situation

Momentan sind zwei separate APIs im Einsatz:

1. **Haupt-API** (`http://localhost:8000`):
   - Allgemeine Backend-API
   - Liefert die meisten Daten für das Frontend

2. **Drift-API** (`http://localhost:8081`):
   - Spezialisierte API für ML-Operationen
   - Liefert Model-Drift-Metriken und Pipeline-Ausführungsdaten

## Integrationsplan

### 1. Endpunkte transferieren

Alle Endpunkte aus `drift_api.py` in die Haupt-API in `src/main.py` integrieren:

- `/api/mlops/models/{model_name}/drift`
- `/api/mlops/pipelines`
- `/api/mlops/pipelines/{pipeline_id}`
- `/api/mlops/pipelines/{pipeline_id}/executions`
- `/api/mlops/pipelines/{pipeline_id}/execute`

### 2. Modelle und Hilfsfunktionen übernehmen

- Die Pydantic-Modelle (`DriftMetrics`, `PipelineExecution`) übernehmen
- Hilfsfunktionen für das Abrufen von Drift-Metriken und Pipeline-Daten migrieren

### 3. Frontend anpassen

Das Frontend so aktualisieren, dass es nur noch eine API-URL verwendet:

```javascript
// Alte Version mit zwei separaten APIs:
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const DRIFT_API_URL = process.env.REACT_APP_DRIFT_API_URL || 'http://localhost:8081';

// Neue Version mit einer integrierten API:
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

Alle API-Aufrufe, die derzeit `driftApi` verwenden, auf `api` umstellen.

### 4. Deployment-Prozess vereinfachen

- Nur noch einen Dienst auf Railway deployen
- Die Frontend-Umgebungsvariablen entsprechend aktualisieren

## Vorteile der Integration

1. **Einfachere Wartung**: Nur noch eine API-Codebasis zu pflegen
2. **Reduzierte Komplexität**: Keine separate Konfiguration für mehrere APIs
3. **Besseres Debugging**: Alle Logs an einem Ort
4. **Besseres Frontend-Erlebnis**: Keine CORS-Probleme durch verschiedene API-Domains

## Implementierungsschritte

1. Die Endpunkte aus `drift_api.py` in `src/main.py` kopieren
2. Tests durchführen, um die korrekte Funktionalität sicherzustellen
3. Frontend-Code anpassen
4. Auf Railway deployen und testen
5. Nach erfolgreicher Validierung die separate Drift-API entfernen 