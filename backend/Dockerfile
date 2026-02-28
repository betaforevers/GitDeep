FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install celery redis

COPY . .

# Expose the API port
EXPOSE 8000

# Default command runs the API, but can be overridden for celery
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
