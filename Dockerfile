FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY setup.py .
RUN pip install -e .

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed logs

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "src/api.py"]
