FROM python:3.11-slim

WORKDIR /app


COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc libpq-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*


COPY . .


ENV PYTHONPATH=/app


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


