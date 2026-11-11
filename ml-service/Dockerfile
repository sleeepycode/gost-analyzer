# ML Service (DO-03)
# Port: 8001 | Health: GET /health
# Тяжёлые deps: OCR (Paddle/EasyOCR), scikit-learn
# Torch — CPU-only (без CUDA), иначе образ раздувается на несколько GB

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    IMAGE_ANALYSIS_MODE=fast \
    MAX_OCR_IMAGES=0 \
    ENABLE_IMAGE_AI=false \
    AI_PROVIDER=ollama \
    OLLAMA_BASE_URL=http://127.0.0.1:11434

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY ml ./ml

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
