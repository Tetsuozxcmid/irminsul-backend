FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

