FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by PaddleOCR and PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "core.celery_app:celery_app", "worker", "-Q", "index_queue,search_queue", "--loglevel=info", "--concurrency=2"]
