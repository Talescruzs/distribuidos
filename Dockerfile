FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY README.md ./README.md
COPY .env.example ./

ENV PYTHONUNBUFFERED=1

EXPOSE 5000
