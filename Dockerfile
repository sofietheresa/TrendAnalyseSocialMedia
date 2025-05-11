FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    software-properties-common \
    wget \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# ⬇️ Wichtig: requirements.txt zuerst kopieren, damit setup.py sie lesen kann
COPY requirements.txt .
COPY setup.py .

# Install project dependencies
RUN pip install --no-cache-dir -e .

# Install Playwright and its dependencies
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps

# Copy the rest of the application
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p data/raw data/processed logs && \
    chmod -R 777 data logs

# Expose port
EXPOSE 10000

# Run app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]
