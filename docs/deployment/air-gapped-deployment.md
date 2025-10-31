# Air-Gapped Deployment Guide

**Version**: 1.0
**Last Updated**: 2025-10-31
**Requirement**: FR-001 (Air-gapped deployment for local government)

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Preparation (Online System)](#preparation-online-system)
4. [Transfer to Target System](#transfer-to-target-system)
5. [Installation (Offline System)](#installation-offline-system)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides step-by-step instructions for deploying the Local LLM Web Application in a completely air-gapped environment with **no internet connectivity**.

**Key Features**:
- No external network dependencies
- All models and dependencies bundled
- Reproducible offline installation
- Suitable for classified government networks

**What is bundled**:
- LLM model files (~2GB, GGUF format)
- Embedding model files (~470MB, sentence-transformers)
- Python dependencies (wheels)
- Node.js dependencies (node_modules)
- Docker images (optional)
- Application source code
- Documentation

---

## Prerequisites

### Online Preparation System (Internet-connected)

**Hardware**:
- Minimum 50GB free disk space (for downloading)
- USB drive or external storage (100GB+ recommended)

**Software**:
- Python 3.11+
- Node.js 18+
- Docker 24+
- Docker Compose 2.0+
- git

### Target Deployment System (Air-gapped)

**Hardware** (FR-002):
- CPU: 8+ cores (16+ recommended)
- RAM: 16GB minimum (32GB recommended)
- Storage: 100GB free space
- GPU: Optional (NVIDIA with 8GB+ VRAM for faster inference)

**Software**:
- Ubuntu 22.04 LTS or similar Linux distribution
- Docker 24+ installed
- Docker Compose 2.0+ installed
- Python 3.11+ installed
- Node.js 18+ installed

**No internet connectivity required!**

---

## Preparation (Online System)

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/local-llm-webapp.git
cd local-llm-webapp
```

### Step 2: Download LLM Model

Download the Qwen 2.5 3B Instruct model (4-bit quantized GGUF):

```bash
mkdir -p models

# Option 1: Using huggingface-cli
pip install huggingface-hub
huggingface-cli download \
  Qwen/Qwen2.5-3B-Instruct-GGUF \
  qwen2.5-3b-instruct-q4_k_m.gguf \
  --local-dir models/

# Option 2: Manual download from HuggingFace
# Visit: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF
# Download: qwen2.5-3b-instruct-q4_k_m.gguf
# Save to: models/qwen2.5-3b-instruct-q4_k_m.gguf
```

**Verify model**:
```bash
ls -lh models/qwen2.5-3b-instruct-q4_k_m.gguf
# Should show ~2GB file
```

### Step 3: Download Embedding Model

```bash
python3 << EOF
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
model.save('models/paraphrase-multilingual-MiniLM-L12-v2')
print("Embedding model downloaded")
EOF
```

**Verify embedding model**:
```bash
ls -la models/paraphrase-multilingual-MiniLM-L12-v2/
# Should contain: config.json, pytorch_model.bin, tokenizer files
```

### Step 4: Download Python Dependencies

```bash
cd backend

# Create wheels directory
mkdir -p wheels

# Download all dependencies as wheels
pip download -r requirements.txt -d wheels/

# Verify downloads
ls wheels/ | wc -l
# Should show 50+ wheel/tar.gz files

cd ..
```

**Alternative**: Use `verify_python_dependencies.py`:
```bash
python3 backend/verify_python_dependencies.py
```

### Step 5: Install Node.js Dependencies

```bash
cd frontend

# Install dependencies (creates node_modules/)
npm install

# Verify installation
ls -la node_modules/ | wc -l
# Should show 1000+ packages

cd ..
```

**Alternative**: Use `verify-node-dependencies.js`:
```bash
node frontend/verify-node-dependencies.js
```

### Step 6: Build Docker Images (Optional)

Pre-building Docker images speeds up offline installation:

```bash
# Build all images
docker-compose build

# Save images to tar files
mkdir -p docker/images

docker save -o docker/images/postgres.tar postgres:15
docker save -o docker/images/backend.tar local-llm-webapp-backend
docker save -o docker/images/frontend.tar local-llm-webapp-frontend

# Verify images
ls -lh docker/images/
# Should show 3 .tar files
```

### Step 7: Create Bundle Archive

Create a single archive for transfer:

```bash
# From project root
tar -czf llm-webapp-offline-bundle.tar.gz \
  backend/ \
  frontend/ \
  models/ \
  docs/ \
  scripts/ \
  docker-compose.yml \
  .env.example \
  README.md

# Verify archive
ls -lh llm-webapp-offline-bundle.tar.gz
# Should show 5-10GB file (depending on Docker images)
```

**Alternative**: Create separate archives:
```bash
# Models (largest)
tar -czf models.tar.gz models/

# Backend dependencies
tar -czf backend-deps.tar.gz backend/wheels/

# Frontend dependencies
tar -czf frontend-deps.tar.gz frontend/node_modules/

# Application code
tar -czf app-code.tar.gz backend/app/ frontend/src/ docker-compose.yml

# Docker images (if built)
tar -czf docker-images.tar.gz docker/images/
```

---

## Transfer to Target System

### Option 1: USB Drive

```bash
# On online system
cp llm-webapp-offline-bundle.tar.gz /media/usb/

# Safely eject
sync
umount /media/usb
```

### Option 2: Network Transfer (if available)

If the target system has an isolated internal network:

```bash
# Using scp (secure copy)
scp llm-webapp-offline-bundle.tar.gz user@target-system:/tmp/

# Using rsync
rsync -avz --progress llm-webapp-offline-bundle.tar.gz user@target-system:/tmp/
```

### Option 3: Physical Media

For highly classified environments:
- Burn to DVD (multi-disc for large bundles)
- Use encrypted external hard drive
- Follow your organization's data transfer protocols

---

## Installation (Offline System)

### Step 1: Verify Air-Gapped Environment

```bash
# Test internet connectivity (should FAIL)
ping -c 3 8.8.8.8
# Expected: "Network is unreachable" or timeout

# Verify DNS is disabled
nslookup google.com
# Expected: "server can't find google.com"
```

**If internet is detected**: Physically disconnect network cable or disable network interface.

### Step 2: Extract Bundle

```bash
# Navigate to deployment location
cd /opt/llm-webapp

# Extract archive
tar -xzf /tmp/llm-webapp-offline-bundle.tar.gz

# Verify extraction
ls -la
# Should show: backend/, frontend/, models/, docs/, etc.
```

### Step 3: Run Offline Installation Script

```bash
# Make script executable
chmod +x scripts/offline-install.sh

# Run installation
./scripts/offline-install.sh
```

**The script will**:
1. Verify offline environment
2. Check prerequisites (Docker, Python, Node.js)
3. Verify bundled files (models, dependencies)
4. Install Python dependencies from wheels/
5. Install Node.js dependencies from node_modules/
6. Load Docker images (if available)
7. Setup environment (.env)
8. Initialize database
9. Build and start services
10. Verify installation

**Expected output**:
```
==========================================
Installation Complete!
==========================================
 Local LLM Web Application installed successfully

Access the application:
  - Frontend: http://localhost:3000
  - Backend API: http://localhost:8000
```

### Step 4: Manual Installation (Alternative)

If the automated script fails, follow these manual steps:

#### 4a. Install Python Dependencies

```bash
cd backend

# Install from bundled wheels (offline)
python3 -m pip install \
  --no-index \
  --find-links=wheels \
  -r requirements.txt

# Verify installation
python3 -c "import fastapi; import transformers; print('Success')"

cd ..
```

#### 4b. Setup Frontend

```bash
cd frontend

# Node modules already bundled - just verify
node -e "require('next'); console.log('Success')"

# Build application
npm run build --offline

cd ..
```

#### 4c. Setup Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (use vim, nano, etc.)
vim .env

# Required settings:
# - DATABASE_URL
# - SECRET_KEY (generate random string)
# - GGUF_MODEL_PATH
```

#### 4d. Initialize Database

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for database to be ready
sleep 10

# Run migrations
cd backend
python3 -m alembic upgrade head
cd ..
```

#### 4e. Start Services

```bash
# Build images (if not pre-loaded)
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
# All services should show "Up"
```

---

## Verification

### Automated Verification

Run the comprehensive verification checklist:

```bash
# Use the checklist from T216
cat docs/deployment/air-gapped-verification-checklist.md
```

Go through each section and verify:
-  Dependencies bundled
-  Models loaded
-  Database initialized
-  Services running
-  Features working

### Manual Verification

#### Test 1: Model Loading

```bash
# Test LLM model loading
python3 backend/test_offline_model_loading.py
# Expected: "OFFLINE MODEL LOADING TEST: PASSED "

# Test embedding model loading
python3 backend/test_offline_embedding_loading.py
# Expected: "OFFLINE EMBEDDING MODEL LOADING TEST: PASSED "
```

#### Test 2: Backend Health

```bash
# Check basic health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Check detailed health
curl http://localhost:8000/health/detailed
# Expected: All components "healthy"
```

#### Test 3: Frontend Access

```bash
# Test frontend
curl http://localhost:3000
# Expected: HTML content (React app)

# Open in browser
firefox http://localhost:3000
# Expected: Setup wizard or login page
```

#### Test 4: End-to-End Chat

1. Navigate to http://localhost:3000
2. Complete admin setup wizard
3. Login
4. Send test message: "HUX8”" (Hello in Korean)
5. Verify Korean response received
6. Check response time < 30 seconds

#### Test 5: Advanced Features

```bash
# Test safety filter
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test profanity: •$"}' \
  -b cookies.txt

# Test document upload
curl -X POST http://localhost:8000/api/v1/documents \
  -F "file=@test.pdf" \
  -b cookies.txt

# Test audit logs (admin only)
curl http://localhost:8000/api/v1/audit-logs \
  -b admin_cookies.txt
```

---

## Troubleshooting

### Issue: "Model file not found"

**Symptom**: Backend fails to start with "Model file not found" error

**Solution**:
```bash
# Verify model file exists
ls -lh models/qwen2.5-3b-instruct-q4_k_m.gguf

# Check .env configuration
grep GGUF_MODEL_PATH .env

# Update path if needed
export GGUF_MODEL_PATH="$(pwd)/models/qwen2.5-3b-instruct-q4_k_m.gguf"
```

### Issue: "Cannot find module 'X'"

**Symptom**: Python or Node.js import errors

**Solution**:
```bash
# For Python
cd backend
python3 -m pip list  # Check installed packages
python3 verify_python_dependencies.py  # Re-run verification

# For Node.js
cd frontend
npm list  # Check installed packages
node verify-node-dependencies.js  # Re-run verification
```

### Issue: "Network error" or "DNS lookup failed"

**Symptom**: Services trying to access internet

**Solution**:
```bash
# Set offline environment variables
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export NPM_CONFIG_OFFLINE=true

# Restart services
docker-compose restart
```

### Issue: Docker build fails

**Symptom**: "Cannot pull image" or network errors during build

**Solution**:
```bash
# Use pre-built images
docker load -i docker/images/backend.tar
docker load -i docker/images/frontend.tar
docker load -i docker/images/postgres.tar

# Verify images loaded
docker images
```

### Issue: Database connection fails

**Symptom**: Backend cannot connect to PostgreSQL

**Solution**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
sleep 10

# Re-run migrations
cd backend
python3 -m alembic upgrade head
```

### Issue: Slow inference (>60s per query)

**Symptom**: LLM responses take too long

**Solution**:
```bash
# Check system resources
htop  # CPU usage
free -h  # Memory usage

# Reduce model context size (edit .env)
# Add: MAX_CONTEXT_LENGTH=512

# Enable GPU if available
# Edit docker-compose.yml: Add nvidia runtime

# Consider using smaller model
# Use Qwen 1.5B instead of 3B
```

### Issue: Permission denied errors

**Symptom**: "Permission denied" when accessing files

**Solution**:
```bash
# Fix file permissions
chmod -R 755 backend/ frontend/ scripts/
chmod +x scripts/*.sh

# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock
```

---

## Post-Installation

### Backup Configuration

```bash
# Backup critical files
mkdir -p backups/config
cp .env backups/config/
cp -r backend/alembic/versions/ backups/config/
```

### Monitor Services

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend

# Check resource usage
docker stats
```

### Regular Maintenance

1. **Daily**: Check disk space and logs
2. **Weekly**: Run database backups (see backup-restore-guide.md)
3. **Monthly**: Review audit logs and usage statistics

### Security Hardening

For production deployment:

1. Change default admin password
2. Review firewall rules (allow only necessary ports)
3. Enable HTTPS (generate self-signed certificate)
4. Implement regular backup schedule
5. Review and customize safety filter rules

---

## Compliance

**FR-001 (Air-gapped deployment)**:  Satisfied
- No internet connectivity required
- All dependencies bundled
- Offline verification successful

**Constitutional Requirements**:
- Korean language support (FR-014): 
- Data isolation (FR-032): 
- Privacy protection (FR-056): 
- Admin privilege isolation (FR-033): 

---

## Support

For issues not covered in this guide:

1. Check other documentation:
   - `docs/user/user-guide-ko.md` (Korean user guide)
   - `docs/admin/advanced-features-manual.md` (Admin manual)
   - `docs/deployment/deployment-guide.md` (General deployment)

2. Review logs:
   - `docker-compose logs`
   - `backend/logs/`

3. Run verification tests:
   - `backend/test_offline_model_loading.py`
   - `backend/verify_python_dependencies.py`
   - `frontend/verify-node-dependencies.js`

4. Contact your system administrator

---

**Document End**
