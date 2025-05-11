FROM python:3.11-slim

# Set working directory
WORKDIR /app

# System dependencies & Playwright browser deps (minimal + cleanup)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcb1 \
    libxkbcommon0 libatspi2.0-0 libx11-6 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libasound2 curl wget gnupg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install pip upgrades & Playwright (inkl. chromium)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir playwright \
    && playwright install --with-deps chromium

# Copy requirements/setup before rest (Docker cache optimization)
COPY requirements.txt setup.py ./

# Install project in editable mode
RUN pip install --no-cache-dir -e .

# Copy remaining project files
COPY . .

# Create necessary directories and set safe permissions
RUN mkdir -p data/raw data/processed logs && \
    chmod -R 777 data logs

# Expose app port
EXPOSE 10000

# Start API
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]
