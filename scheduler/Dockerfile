FROM python:3.11-slim

# Arbeitsverzeichnis
WORKDIR /app

# Requirements kopieren & installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Alle Skripte rein
COPY app/src/ ./

# Cron vorbereiten
RUN apt-get update && \
    apt-get install -y cron && \
    rm -rf /var/lib/apt/lists/*

# Die Log-Datei vorbereiten und Container aktiv halten
CMD touch /app/logs/cron.log && cron && tail -f /app/logs/cron.log
