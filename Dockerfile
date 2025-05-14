# Base image: leichter Python-Slim
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only essential system dependencies (none hier nötig!)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy only what’s needed first (für besseren Docker Cache)
COPY requirements.txt ./

# Install Python requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy only required project folders (nicht das ganze Projekt!)
COPY app/ ./app/
COPY models/ ./models/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create persistent folders (SQLite/Logs etc.)
RUN mkdir -p /app/data/processed /app/logs && \
    chmod -R 777 /app/data /app/logs

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
