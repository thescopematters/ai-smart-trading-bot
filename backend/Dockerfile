FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak \
    libespeak1 \
    git \
    cmake \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

COPY . .

# Whisper.cpp build
RUN git clone https://github.com/ggerganov/whisper.cpp.git /app/whisper.cpp && \
    cd /app/whisper.cpp && \
    cmake -B build && \
    cmake --build build --config Release && \
    bash models/download-ggml-model.sh base.en

EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]