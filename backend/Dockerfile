# ============================================
# STAGE 1: Builder — compile whisper.cpp and
# install all Python dependencies
# ============================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build-time-only tools (git, cmake, gcc, etc.) with --no-install-recommends
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    cmake \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# ── Whisper.cpp: clone, compile, and download model ──
RUN git clone https://github.com/ggerganov/whisper.cpp.git /build/whisper.cpp && \
    cd /build/whisper.cpp && \
    cmake -B build && \
    cmake --build build --config Release && \
    bash models/download-ggml-model.sh base.en

# ── Python deps: install CPU-only PyTorch, then rest, then strip GPU-specific triton ──
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --default-timeout=100 --no-cache-dir -r requirements.txt && \
    pip uninstall -y triton

# ============================================
# STAGE 2: Production — lightweight runtime
# ============================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install only the essential runtime libraries with --no-install-recommends
# (Saves massive space by not pulling in recommended/suggested GUI/X11 dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    espeak \
    libespeak1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Copy compiled whisper.cpp binary + model from builder ──
COPY --from=builder /build/whisper.cpp/build/bin/whisper-cli /app/whisper.cpp/build/bin/whisper-cli
COPY --from=builder /build/whisper.cpp/models/ggml-base.en.bin /app/whisper.cpp/models/ggml-base.en.bin

# ── Copy all installed Python packages from builder ──
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# ── Copy application source code ──
COPY . .

EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]