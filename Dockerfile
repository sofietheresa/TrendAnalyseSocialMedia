FROM python:3.11-slim-bullseye as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim-bullseye as runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install PostgreSQL client libraries and other essential dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy only the installed Python packages
COPY --from=builder /root/.local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy the application code
COPY ./src /app/src 
COPY ./start.py /app/start.py
# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/models

EXPOSE 8000

# Use a script to wait for the database and then start the application
CMD ["python", "start.py"]



