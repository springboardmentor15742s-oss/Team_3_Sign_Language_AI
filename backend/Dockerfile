FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# opencv-python (non-headless, per requirements.txt) dynamically links
# against these system libs at import time — without them, `import cv2`
# fails with "libGL.so.1: cannot open shared object file".
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# MediaPipe's hand landmark model. Not tracked in git (see .gitignore), so
# it's fetched here at build time from the same official source used to set
# it up originally, rather than relying on it already being present in the
# build context — keeps the image self-contained for a fresh clone.
RUN mkdir -p data/models && \
    curl -sSL -o data/models/hand_landmarker.task \
    https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
