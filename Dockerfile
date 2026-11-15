# ==========================================
# STAGE 1: Build Frontend (Vite + React)
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/Frontend

COPY Frontend/package*.json ./
RUN npm install

COPY Frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Python Backend with ML Models
# ==========================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8000

# Install system libraries needed by OpenCV and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch CPU first to avoid downloading 4GB+ CUDA wheels in cloud
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY Backend/requirements.txt ./Backend/
RUN pip install --no-cache-dir -r Backend/requirements.txt

# Copy Backend application and models
COPY Backend/ ./Backend/

# Copy built Frontend static files from Stage 1
COPY --from=frontend-builder /app/Frontend/dist ./Frontend/dist

WORKDIR /app/Backend

EXPOSE 8000

# Run FastAPI serving both API and Frontend
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
