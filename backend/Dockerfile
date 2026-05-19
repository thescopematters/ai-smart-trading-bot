# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git cmake curl wget build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# ── whisper.cpp: shallow clone + build only the CLI target ──
RUN git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git /build/whisper.cpp && \
    cd /build/whisper.cpp && \
    cmake -B build \
        -DBUILD_SHARED_LIBS=OFF \
        -DWHISPER_BUILD_TESTS=OFF \
        -DWHISPER_BUILD_EXAMPLES=OFF && \
    cmake --build build --config Release --target whisper-cli && \
    bash models/download-ggml-model.sh base.en

# ── Python deps ──
COPY requirements.txt .

# ── FIX 2: Pre-pin to /install so pip respects them when resolving requirements ──
RUN pip install --no-cache-dir --prefix=/install \
    "pyarrow==14.0.2" \
    "onnxruntime==1.17.3"

# Install everything into /install prefix
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Surgical cleanup ──
# ── FIX 1: Correct find syntax for .pyc/.pyo ──
RUN find /install -type d -name "kubernetes"              -exec rm -rf {} + 2>/dev/null || true && \
    find /install -type d -name "vertexai"                -exec rm -rf {} + 2>/dev/null || true && \
    find /install -type d -name "google_cloud_aiplatform" -exec rm -rf {} + 2>/dev/null || true && \
    find /install -type d -name "tests"                   -exec rm -rf {} + 2>/dev/null || true && \
    find /install -type d -name "__pycache__"             -exec rm -rf {} + 2>/dev/null || true && \
    find /install \( -name "*.pyc" -o -name "*.pyo" \)    -exec rm -f  {} + 2>/dev/null || true


# ============================================
# STAGE 2: Production
# ============================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# ── Static ffmpeg (~70 MB vs apt's 464 MB) ──
RUN curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    | tar -xJ --strip-components=1 -C /usr/local/bin \
        --wildcards "*/ffmpeg" "*/ffprobe" && \
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

WORKDIR /app

# ── Whisper binary + model ──
COPY --from=builder /build/whisper.cpp/build/bin/whisper-cli \
    /app/whisper.cpp/build/bin/whisper-cli
COPY --from=builder /build/whisper.cpp/models/ggml-base.en.bin \
    /app/whisper.cpp/models/ggml-base.en.bin

# ── Python site-packages ──
COPY --from=builder /install/lib/python3.11/site-packages \
    /usr/local/lib/python3.11/site-packages

# ── FIX 3: Copy all installed bin entries, not just uvicorn ──
COPY --from=builder /install/bin /usr/local/bin

# ── App source (last = best cache behaviour) ──
COPY . .

EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]