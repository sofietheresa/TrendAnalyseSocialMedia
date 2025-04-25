FROM python:3.10-slim

# Set working directory
WORKDIR /app

# System-Tools
RUN apt-get update && apt-get install -y cron procps  bash coreutils

# Projekt-Code reinkopieren
COPY app/ /app/                 
COPY scheduler/crontab /etc/cron.d/scraper-cron
COPY scheduler/start.sh /start.sh
COPY scheduler/run_all_scrapers.py /app/src/run_all_scrapers.py
COPY requirements.txt .

# Cron-Datei einrichten
RUN chmod 0644 /etc/cron.d/scraper-cron
RUN crontab /etc/cron.d/scraper-cron

# Cron-Log vorbereiten
RUN touch /var/log/cron.log

# Python-Dependencies installieren
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps


# Startskript ausführbar machen
RUN chmod +x /start.sh

# Start
CMD ["/bin/bash", "/start.sh"]
