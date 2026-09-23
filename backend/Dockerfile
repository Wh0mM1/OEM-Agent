# Python 3.11 slim base image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install curl and build utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency specifications first for optimal layer caching
COPY pyproject.toml uv.lock ./

# Install project dependencies using uv
RUN uv sync --frozen

# Copy backend source code
COPY . .

# Expose FastAPI backend port
EXPOSE 8000

# Run FastAPI server
CMD ["uv", "run", "python", "main.py"]
