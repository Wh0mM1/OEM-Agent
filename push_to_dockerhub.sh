#!/usr/bin/env bash
set -e

# ==============================================================================
# Build and Push Mahindra OEM AI Concierge Images to Docker Hub
# ==============================================================================

DOCKER_USER="wh0mm1"
BACKEND_TAG="${DOCKER_USER}/mahindra-oem-backend:latest"
FRONTEND_TAG="${DOCKER_USER}/mahindra-oem-frontend:latest"

echo "======================================================================"
echo "  Target Docker Hub Namespace: ${DOCKER_USER}"
echo "======================================================================"

# 1. Check Docker daemon
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running."
    echo "Please start Docker Desktop or your container runtime and try again."
    exit 1
fi

# 2. Build backend
echo ""
echo "--> [1/4] Building Backend image (${BACKEND_TAG})..."
docker build -t "${BACKEND_TAG}" ./backend

# 3. Build frontend
echo ""
echo "--> [2/4] Building Frontend image (${FRONTEND_TAG})..."
docker build -t "${FRONTEND_TAG}" ./frontend

# 4. Push backend
echo ""
echo "--> [3/4] Pushing Backend image to Docker Hub..."
docker push "${BACKEND_TAG}"

# 5. Push frontend
echo ""
echo "--> [4/4] Pushing Frontend image to Docker Hub..."
docker push "${FRONTEND_TAG}"

echo ""
echo "======================================================================"
echo "  SUCCESS: All images built and pushed to Docker Hub!"
echo "  - ${BACKEND_TAG}"
echo "  - ${FRONTEND_TAG}"
echo "======================================================================"
