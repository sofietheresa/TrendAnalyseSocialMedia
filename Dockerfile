FROM python:3.11-slim

# Systemabhängigkeiten für Playwright-Browser
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libxfixes3 \
    libxext6 \
    libx11-6 \
    fonts-liberation \
    libappindicator3-1 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 🟢 Playwright-Browser installieren
RUN python -m playwright install --with-deps

# App kopieren
COPY api/ api/
COPY scheduler/ scheduler/

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "10000"]
