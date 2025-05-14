FROM python:3.11-slim-bullseye

# Set working directory
WORKDIR /app

# Nur benötigte Systempakete installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcb1 \
    libxkbcommon0 libatspi2.0-0 libx11-6 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libasound2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install pip & playwright
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir playwright \
    && playwright install --with-deps chromium

# Requirements separat kopieren für Caching
COPY requirements.txt setup.py ./

# Dependencies installieren
RUN pip install --no-cache-dir -e .

# Dann erst Quellcode (damit Caching greift)
COPY . .

# Verzeichnisse vorbereiten
RUN mkdir -p data/raw data/processed logs && \
    chmod -R 777 data logs

# Expose Port
EXPOSE 10000

# Start FastAPI mit Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]
