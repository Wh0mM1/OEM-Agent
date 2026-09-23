# ==============================================================================
# Multi-Stage Dockerfile for Hugging Face Spaces & Production Deployments
# Stage 1: Build React 18 TypeScript Frontend
# Stage 2: Python 3.11 Backend Service + Static Asset Server (Port 7860)
# ==============================================================================

# --- Stage 1: Frontend Build ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python Backend Service ---
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HOST=0.0.0.0

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency specifications and sync
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen

# Copy backend application source
COPY backend/ ./

# Copy compiled React frontend assets into static_dist for FastAPI serving
COPY --from=frontend-builder /app/frontend/dist /app/static_dist

# Set up non-root user (Hugging Face Spaces standard: UID 1000)
RUN useradd -m -u 1000 user && \
    chown -R user:user /app
USER user

# Expose Hugging Face Space default port
EXPOSE 7860

# Run FastAPI with uvicorn on port 7860
CMD ["uv", "run", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "7860"]
