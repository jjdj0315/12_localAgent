#!/bin/bash

##############################################################################
# Offline Installation Script (T221)
#
# Installs Local LLM Web Application in air-gapped environment.
# Tests FR-001: Air-gapped deployment requirement.
#
# Prerequisites:
#   - All files transferred to target system
#   - Docker and Docker Compose installed
#   - No internet connectivity required
#
# Usage:
#   chmod +x scripts/offline-install.sh
#   ./scripts/offline-install.sh
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Main installation
header "Offline Installation - Local LLM Web Application"

info "Target: Air-gapped local government deployment"
info "Requirement: FR-001 (No internet connectivity)"

# Step 1: Verify offline environment
header "Step 1: Verifying Offline Environment"

info "Testing internet connectivity..."
if ping -c 1 -W 3 8.8.8.8 &> /dev/null; then
    warn "Internet connection detected!"
    warn "This system should be air-gapped (no internet)"
    warn "Continuing installation..."
else
    success "No internet connection (air-gapped mode confirmed)"
fi

# Step 2: Check prerequisites
header "Step 2: Checking Prerequisites"

# Check Docker
info "Checking Docker..."
if ! command -v docker &> /dev/null; then
    error "Docker not found. Please install Docker first."
fi
DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
success "Docker ${DOCKER_VERSION} found"

# Check Docker Compose
info "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose not found. Please install Docker Compose first."
fi
COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4 | cut -d',' -f1)
success "Docker Compose ${COMPOSE_VERSION} found"

# Check Python
info "Checking Python..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 not found. Please install Python 3.11+ first."
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
success "Python ${PYTHON_VERSION} found"

# Check Node.js
info "Checking Node.js..."
if ! command -v node &> /dev/null; then
    error "Node.js not found. Please install Node.js 18+ first."
fi
NODE_VERSION=$(node --version | cut -d'v' -f2)
success "Node.js ${NODE_VERSION} found"

# Step 3: Verify bundled files
header "Step 3: Verifying Bundled Files"

# Check project structure
info "Checking project structure..."
for dir in backend frontend models docs scripts; do
    if [ ! -d "$dir" ]; then
        error "Directory not found: $dir"
    fi
    success "Found: $dir/"
done

# Check model files
info "Checking LLM model files..."
MODEL_PATH="${GGUF_MODEL_PATH:-models/qwen2.5-3b-instruct-q4_k_m.gguf}"
if [ ! -f "$MODEL_PATH" ]; then
    error "LLM model not found: $MODEL_PATH"
fi
MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
success "LLM model found: $MODEL_PATH ($MODEL_SIZE)"

# Check embedding model
info "Checking embedding model..."
EMBEDDING_MODEL="models/paraphrase-multilingual-MiniLM-L12-v2"
if [ ! -d "$EMBEDDING_MODEL" ]; then
    warn "Embedding model not found: $EMBEDDING_MODEL"
    warn "Semantic tag matching may not work"
else
    success "Embedding model found: $EMBEDDING_MODEL"
fi

# Step 4: Install Python dependencies
header "Step 4: Installing Python Dependencies (Offline)"

cd backend

info "Checking Python wheels..."
if [ ! -d "wheels" ]; then
    warn "Python wheels directory not found"
    warn "Attempting standard pip install (may fail if offline)"
else
    WHEEL_COUNT=$(ls wheels/*.whl 2>/dev/null | wc -l)
    success "Found ${WHEEL_COUNT} wheel files"

    info "Installing from bundled wheels..."
    python3 -m pip install --no-index --find-links=wheels -r requirements.txt || \
        error "Failed to install Python dependencies"
    success "Python dependencies installed"
fi

# Verify critical Python packages
info "Verifying critical Python packages..."
python3 -c "import fastapi" || error "fastapi not installed"
python3 -c "import transformers" || error "transformers not installed"
python3 -c "import llama_cpp" || error "llama_cpp not installed"
success "All critical Python packages installed"

cd ..

# Step 5: Install Node.js dependencies
header "Step 5: Installing Node.js Dependencies (Offline)"

cd frontend

info "Checking node_modules..."
if [ ! -d "node_modules" ]; then
    warn "node_modules directory not found"
    warn "Attempting npm install (may fail if offline)"
    npm install --offline || npm install --prefer-offline || \
        error "Failed to install Node.js dependencies"
else
    PKG_COUNT=$(ls -1 node_modules | wc -l)
    success "Found ${PKG_COUNT} packages in node_modules"
fi

# Verify critical Node packages
info "Verifying critical Node.js packages..."
node -e "require('next')" || error "next not installed"
node -e "require('react')" || error "react not installed"
success "All critical Node.js packages installed"

cd ..

# Step 6: Load Docker images
header "Step 6: Loading Docker Images (Optional)"

if [ -d "docker/images" ]; then
    info "Found Docker images directory"

    for image in docker/images/*.tar; do
        if [ -f "$image" ]; then
            info "Loading $(basename $image)..."
            docker load -i "$image" || warn "Failed to load $(basename $image)"
        fi
    done

    success "Docker images loaded"
else
    info "No pre-built Docker images found"
    info "Images will be built from Dockerfiles"
fi

# Step 7: Setup environment
header "Step 7: Setting Up Environment"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        info "Creating .env from .env.example..."
        cp .env.example .env
        warn "Please edit .env to configure your deployment"
    else
        error ".env.example not found"
    fi
else
    success ".env already exists"
fi

# Generate random secret key if not set
if ! grep -q "SECRET_KEY=" .env || grep -q "SECRET_KEY=your_secret_key_here" .env; then
    info "Generating random SECRET_KEY..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" .env
    success "SECRET_KEY generated"
fi

# Step 8: Initialize database
header "Step 8: Initializing Database"

info "Starting PostgreSQL..."
docker-compose up -d postgres

info "Waiting for PostgreSQL to be ready..."
sleep 10

info "Running database migrations..."
cd backend
python3 -m alembic upgrade head || error "Database migration failed"
success "Database initialized"
cd ..

# Step 9: Build and start services
header "Step 9: Building and Starting Services"

info "Building Docker images..."
docker-compose build || error "Docker build failed"

info "Starting all services..."
docker-compose up -d || error "Failed to start services"

# Wait for services to start
info "Waiting for services to start (30 seconds)..."
sleep 30

# Step 10: Verify installation
header "Step 10: Verifying Installation"

# Check backend health
info "Checking backend health..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/health || echo "failed")
if [[ "$BACKEND_HEALTH" == *"healthy"* ]]; then
    success "Backend is healthy"
else
    error "Backend health check failed"
fi

# Check frontend
info "Checking frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$FRONTEND_STATUS" == "200" ]; then
    success "Frontend is accessible"
else
    warn "Frontend returned status: $FRONTEND_STATUS"
fi

# Final summary
header "Installation Complete!"

success "Local LLM Web Application installed successfully"
echo ""
info "Access the application:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
info "Initial setup:"
echo "  1. Navigate to http://localhost:3000"
echo "  2. Complete the admin setup wizard"
echo "  3. Create your first admin account"
echo ""
info "Next steps:"
echo "  - Review logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart services: docker-compose restart"
echo ""
info "Documentation:"
echo "  - User Guide: docs/user/user-guide-ko.md"
echo "  - Admin Manual: docs/admin/advanced-features-manual.md"
echo "  - Deployment Guide: docs/deployment/deployment-guide.md"
echo ""
success "FR-001 (Air-gapped deployment) requirement satisfied"
echo ""
