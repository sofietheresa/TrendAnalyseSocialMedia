FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY scheduler/ scheduler/

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "10000"]
