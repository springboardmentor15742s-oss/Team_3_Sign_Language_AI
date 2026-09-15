# Sign Language Learning & Assessment Platform — Backend (FastAPI)
FROM python:3.12-slim

WORKDIR /app

# System deps: opencv/mediapipe need a few shared libs not in slim by default
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite DB lives here; mount a volume at this path to persist it
# across container restarts/rebuilds.
ENV DB_PATH=/app/data/platform.db
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
