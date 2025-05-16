# Railway API Integration

Diese Dokumentation erklärt, wie die Social Media Trend Analysis Anwendung mit der Railway API konfiguriert wird, um ausschließlich echte Daten zu verwenden.

## API-Konfiguration

Die Frontend-Anwendung wurde aktualisiert, um direkt mit der Railway API zu kommunizieren:

```javascript
// In frontend/src/services/api.js
const API_URL = "https://trendanalysesocialmedia-production.up.railway.app";
const ENABLE_DB_ENDPOINTS = true;
```

## Verwendung echter Daten

Alle API-Endpunkte wurden aktualisiert, sodass:

1. Keine Mock-Daten mehr verwendet werden (`useMockApi = false`)
2. Alle Funktionen greifen direkt auf die funktionierenden Endpunkte der Railway API zu
3. Alle Fallback-Logiken wurden entfernt - es werden nur echte Daten angezeigt
4. Bei Fehlern werden Fehler geworfen statt auf Mock-Daten zurückzugreifen

## Verfügbare API-Endpunkte

Die folgenden bestätigten Railway API-Endpunkte werden verwendet:

- `/health` - System-Gesundheitsstatus
- `/api/scraper-status` - Status der Social-Media-Scraper
- `/api/daily-stats` - Tägliche Statistiken über gesammelte Daten
- `/api/topic-model` - Für Topic-Modelling-Daten (NICHT `/api/db/topic-model`)
- `/api/db/predictions` - Für Vorhersagen und Prognosen
- `/api/mlops/models/{model_name}/versions` - Für Modellversionen
- `/api/mlops/models/{model_name}/metrics` - Für Modellmetriken
- `/api/mlops/models/{model_name}/drift` - Für Modell-Drift-Daten

**Hinweis:** Die Tests haben bestätigt, dass diese Endpunkte funktionieren und echte Daten zurückgeben. 
Alle API-Funktionen wurden entsprechend angepasst.

## Testen der API-Verbindung

Es wurden zwei Test-Skripts erstellt:

1. `npm run test:railway-api` - Testet alle bestätigten funktionierenden Endpunkte
2. `npm run test:railway-api-endpoints` - Testet zusätzliche Endpunkte zur API-Abdeckung

Beispielaufruf:
```
cd frontend
npm run test:railway-api
```

## Starten der Anwendung mit Railway API

Um die Anwendung mit der Railway API zu starten:

```
cd frontend
npm run start:railway
```

Dies setzt die Umgebungsvariablen korrekt und startet das Frontend mit direkter Verbindung zur Railway API.

## Wichtige Erkenntnisse

Die Tests haben gezeigt, dass:

1. Die DB-Endpunkte für Topic-Model, Modellversionen, Metriken und Drift nicht funktionieren
2. Stattdessen müssen die API und MLOps-Endpunkte verwendet werden
3. Die DB-Endpunkte für Vorhersagen funktionieren korrekt
4. Alle API-Funktionen wurden angepasst, um die korrekten, funktionierenden Endpunkte zu verwenden

## Fehlerbehebung

Bei API-Verbindungsproblemen:

1. Überprüfe, ob die Railway API unter https://trendanalysesocialmedia-production.up.railway.app erreichbar ist
2. Führe `npm run test:railway-api` aus, um den Status aller bestätigten Endpunkte zu prüfen
3. Überprüfe die Konsolenausgaben auf spezifische API-Fehler 