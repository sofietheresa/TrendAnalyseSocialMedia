FROM python:3.11-slim

WORKDIR /app

# System-Tools (cron & logging)
RUN apt-get update && \
    apt-get install -y cron && \
    pip install --no-cache-dir --upgrade pip

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app/src ./app/src
COPY scheduler/run_all_scrapers.py ./scheduler/run_all_scrapers.py
COPY cron/crontab /etc/cron.d/socialmedia-cron

# Logs & Rechte
RUN mkdir -p /app/logs && \
    chmod 0644 /etc/cron.d/socialmedia-cron && \
    crontab /etc/cron.d/socialmedia-cron

# Run cron in foreground
CMD ["cron", "-f"]
