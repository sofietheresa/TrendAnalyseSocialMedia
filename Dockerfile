FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Minimaler Systembedarf
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libx11-6 libxcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libxss1 libasound2 libxext6 libxfixes3 libxkbcommon0 libcups2 \
    curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Nur das Nötigste für ML/NLP
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Nur Quellcode
COPY ./src /app/src

# Datenverzeichnisse anlegen
RUN mkdir -p /app/data /app/logs

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
