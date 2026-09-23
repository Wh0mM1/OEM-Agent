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

# 2. Build React production bundle and copy to backend/static_dist
echo ""
echo "--> [1/5] Building React production assets for unified serving..."
(cd frontend && npm run build)
mkdir -p backend/static_dist
cp -r frontend/dist/* backend/static_dist/

# 3. Build backend image
echo ""
echo "--> [2/5] Building Backend image (${BACKEND_TAG})..."
docker build -t "${BACKEND_TAG}" ./backend

# 4. Build frontend image
echo ""
echo "--> [3/5] Building Frontend image (${FRONTEND_TAG})..."
docker build -t "${FRONTEND_TAG}" ./frontend

# 5. Push backend image
echo ""
echo "--> [4/5] Pushing Backend image to Docker Hub..."
docker push "${BACKEND_TAG}"

# 6. Push frontend image
echo ""
echo "--> [5/5] Pushing Frontend image to Docker Hub..."
docker push "${FRONTEND_TAG}"

echo ""
echo "======================================================================"
echo "  SUCCESS: All images built and pushed to Docker Hub!"
echo "  - ${BACKEND_TAG}"
echo "  - ${FRONTEND_TAG}"
echo "======================================================================"
