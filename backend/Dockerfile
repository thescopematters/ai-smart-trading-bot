FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies + build tools for whisper.cpp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak \
    libespeak1 \
    git \
    cmake \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build whisper.cpp from source (only if not already present)
RUN if [ ! -f /app/whisper.cpp/build/bin/whisper-cli ]; then \
    git clone https://github.com/ggerganov/whisper.cpp.git /app/whisper.cpp && \
    cd /app/whisper.cpp && \
    cmake -B build && \
    cmake --build build --config Release && \
    bash models/download-ggml-model.sh base.en; \
    fi

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]