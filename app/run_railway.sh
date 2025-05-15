#!/bin/bash
# Startup-Skript für Railway

echo "Starting Railway deployment..."
echo "Current directory: $(pwd)"

# Port aus Umgebungsvariable übernehmen oder Standard verwenden
PORT=${PORT:-8000}
echo "Using port: $PORT"

# Health-App im Hintergrund starten
echo "Starting health app in the background..."
uvicorn health_app:app --host=0.0.0.0 --port=$PORT &
HEALTH_APP_PID=$!
echo "Health app started with PID: $HEALTH_APP_PID"

# Warte einen Moment, damit die Health-App starten kann
sleep 5

# Hauptanwendung starten
echo "Starting main application..."
python railway.py

# Falls die Hauptanwendung beendet wird, beende auch die Health-App
kill $HEALTH_APP_PID 