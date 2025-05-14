FROM python:3.11-slim-bullseye

# Set working directory
WORKDIR /app

# Systemabhängigkeiten (nur was FastAPI & Modell evtl. braucht)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libxcb1 libx11-6 libasound2 libatk1.0-0 libcups2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Pip und Dependencies installieren
COPY requirements.txt setup.py ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

# Nur benötigten Quellcode kopieren
COPY src/ ./src/

# OPTIONAL: Leeres Verzeichnis vorbereiten für Logs (wird ignoriert)
RUN mkdir -p logs && chmod -R 777 logs

# Expose FastAPI port
EXPOSE 10000

# Starte die App
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]
