FROM python:3.11-slim

WORKDIR /app

# Install only required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app/ /app/app/
COPY models/ /app/models/

# Create necessary directories for data persistence
RUN mkdir -p /app/data/processed && \
    mkdir -p /app/logs && \
    chown -R www-data:www-data /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose FastAPI port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
