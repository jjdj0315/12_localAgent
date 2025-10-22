# Quickstart Guide: Local LLM Web Application

**Target Audience**: Developers and IT administrators setting up the Local LLM web application

**Estimated Setup Time**: 2-4 hours (excluding model download)

---

## Prerequisites

### Hardware Requirements

**Minimum**:
- CPU: 8+ cores (x86_64)
- RAM: 32GB
- GPU: NVIDIA GPU with 16GB+ VRAM (RTX 3090, RTX 4090, A10, L4, etc.)
- Storage: 200GB free space (100GB for models, 100GB for application data)
- Network: Internal network connectivity (air-gapped deployment supported)

**Recommended**:
- CPU: 16+ cores
- RAM: 64GB
- GPU: NVIDIA GPU with 24GB+ VRAM (RTX 4090, A100, etc.)
- Storage: 500GB SSD

### Software Requirements

**On Internet-Connected Machine** (for preparation):
- Docker 24+ with Docker Compose
- Git
- Python 3.11+
- Node.js 18+
- NVIDIA Driver 525+ (for GPU support)
- NVIDIA Container Toolkit

**On Air-Gapped Server** (target deployment):
- Ubuntu 22.04 LTS (or similar Linux distribution)
- Docker 24+ with Docker Compose
- NVIDIA Driver 525+
- NVIDIA Container Toolkit

---

## Quick Start (Development Environment)

### 1. Clone Repository

```bash
git clone <repository-url>
cd local-llm-webapp
```

### 2. Download LLM Model

```bash
# Install Hugging Face CLI
pip install huggingface-hub

# Download Llama-3-8B model (requires ~16GB)
# Note: Requires Llama 3 license acceptance on Hugging Face
huggingface-cli login  # Enter your HF token
huggingface-cli download meta-llama/Meta-Llama-3-8B --local-dir ./models/llama-3-8b

# Alternative: Download quantized version (4-bit GPTQ)
huggingface-cli download TheBloke/Llama-3-8B-GPTQ --local-dir ./models/llama-3-8b-gptq
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Key Environment Variables**:
```bash
# Database
POSTGRES_USER=llm_app
POSTGRES_PASSWORD=<generate-secure-password>
POSTGRES_DB=llm_webapp

# Backend
SECRET_KEY=<generate-random-secret-key>
SESSION_TIMEOUT_MINUTES=30

# LLM Service
MODEL_PATH=/models/llama-3-8b
MAX_MODEL_LEN=4096
GPU_MEMORY_UTILIZATION=0.9
TENSOR_PARALLEL_SIZE=1

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 4. Start Services

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Initialize Database

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Create initial admin user
docker-compose exec backend python scripts/create_admin.py \
  --username admin \
  --password <admin-password>
```

### 6. Access Application

- **Web UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Admin Login**: Use admin credentials created in step 5

---

## Air-Gapped Deployment

### Preparation (Internet-Connected Machine)

#### 1. Build Docker Images

```bash
# Build all images
docker-compose build

# Tag images for export
docker tag local-llm-webapp-frontend:latest llm-frontend:v1.0.0
docker tag local-llm-webapp-backend:latest llm-backend:v1.0.0
docker tag local-llm-webapp-llm-service:latest llm-service:v1.0.0
```

#### 2. Export Docker Images

```bash
# Export frontend image
docker save llm-frontend:v1.0.0 | gzip > llm-frontend-v1.0.0.tar.gz

# Export backend image
docker save llm-backend:v1.0.0 | gzip > llm-backend-v1.0.0.tar.gz

# Export LLM service image
docker save llm-service:v1.0.0 | gzip > llm-service-v1.0.0.tar.gz

# Export PostgreSQL image
docker pull postgres:15
docker save postgres:15 | gzip > postgres-15.tar.gz

# Optional: Export nginx if used
docker pull nginx:alpine
docker save nginx:alpine | gzip > nginx-alpine.tar.gz
```

#### 3. Package Application Files

```bash
# Create deployment package
mkdir -p deployment-package
cp -r docker-compose.yml .env.example deployment-package/
cp -r docker/ deployment-package/
cp -r backend/alembic/ deployment-package/alembic/
cp -r scripts/ deployment-package/

# Copy model files
cp -r models/llama-3-8b deployment-package/models/

# Create tarball
tar -czf llm-webapp-deployment-v1.0.0.tar.gz deployment-package/
```

#### 4. Transfer to Air-Gapped Server

Transfer these files via USB, secure file transfer, or approved method:
- `llm-frontend-v1.0.0.tar.gz`
- `llm-backend-v1.0.0.tar.gz`
- `llm-service-v1.0.0.tar.gz`
- `postgres-15.tar.gz`
- `nginx-alpine.tar.gz` (if using nginx)
- `llm-webapp-deployment-v1.0.0.tar.gz`

### Deployment (Air-Gapped Server)

#### 1. Load Docker Images

```bash
# Load all images
docker load < llm-frontend-v1.0.0.tar.gz
docker load < llm-backend-v1.0.0.tar.gz
docker load < llm-service-v1.0.0.tar.gz
docker load < postgres-15.tar.gz
docker load < nginx-alpine.tar.gz

# Verify images loaded
docker images
```

#### 2. Extract Application Files

```bash
# Extract deployment package
tar -xzf llm-webapp-deployment-v1.0.0.tar.gz
cd deployment-package/
```

#### 3. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env

# Update these values for production:
# - POSTGRES_PASSWORD (generate secure password)
# - SECRET_KEY (generate random 64-character string)
# - NEXT_PUBLIC_API_URL (use actual server IP)
```

#### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs -f

# Wait for services to be healthy (~2-3 minutes for LLM service)
```

#### 5. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create admin user
docker-compose exec backend python scripts/create_admin.py \
  --username admin \
  --password <secure-admin-password>

# Verify admin user created
docker-compose exec backend python scripts/list_users.py
```

#### 6. Create Initial Users

```bash
# Create user accounts for employees
docker-compose exec backend python scripts/create_user.py \
  --username employee001 \
  --password <initial-password>

# Or use admin panel (login as admin at http://<server-ip>:3000/admin)
```

#### 7. Verify Deployment

**Health Checks**:
```bash
# Check backend health
curl http://<server-ip>:8000/api/v1/health

# Check LLM service
curl http://<server-ip>:8001/health

# Check frontend
curl http://<server-ip>:3000
```

**Test LLM Response**:
```bash
# Login and test chat
curl -c cookies.txt -X POST http://<server-ip>:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<admin-password>"}'

curl -b cookies.txt -X POST http://<server-ip>:8000/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": null, "content": "안녕하세요"}'
```

---

## Post-Deployment Configuration

### 1. Configure Firewall

```bash
# Allow internal network access to services
sudo ufw allow from <internal-subnet> to any port 3000  # Frontend
sudo ufw allow from <internal-subnet> to any port 8000  # Backend API

# Block external access
sudo ufw default deny incoming
sudo ufw enable
```

### 2. Set Up Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/llm-webapp

# Add configuration:
/var/lib/docker/containers/*/*.log {
  daily
  rotate 7
  compress
  missingok
  notifempty
  copytruncate
}
```

### 3. Configure Backup

```bash
# Database backup script
cat > backup-database.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=/backups/llm-webapp
DATE=$(date +%Y%m%d-%H%M%S)

docker-compose exec -T postgres pg_dump -U llm_app llm_webapp | \
  gzip > $BACKUP_DIR/db-backup-$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "db-backup-*.sql.gz" -mtime +30 -delete
EOF

chmod +x backup-database.sh

# Add to cron (daily at 2 AM)
(crontab -l ; echo "0 2 * * * /path/to/backup-database.sh") | crontab -
```

### 4. Monitor System Resources

```bash
# Install monitoring tools (if not already installed)
sudo apt install -y htop nvtop  # nvtop for GPU monitoring

# Check GPU usage
nvidia-smi

# Check container resource usage
docker stats
```

---

## Common Operations

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f llm-service

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart llm-service

# Stop and start (clears container state)
docker-compose down
docker-compose up -d
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U llm_app -d llm_webapp

# Run database backup
docker-compose exec postgres pg_dump -U llm_app llm_webapp > backup.sql

# Restore database
docker-compose exec -T postgres psql -U llm_app -d llm_webapp < backup.sql

# Run migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

### User Management

```bash
# Create user
docker-compose exec backend python scripts/create_user.py \
  --username <username> --password <password>

# Reset password
docker-compose exec backend python scripts/reset_password.py \
  --username <username> --password <new-password>

# List all users
docker-compose exec backend python scripts/list_users.py

# Delete user
docker-compose exec backend python scripts/delete_user.py \
  --username <username>
```

### Updating the Application

```bash
# On internet-connected machine: build new images
docker-compose build
docker save <new-image> | gzip > new-image.tar.gz

# Transfer to air-gapped server

# On air-gapped server: load and restart
docker load < new-image.tar.gz
docker-compose down
docker-compose up -d

# Run any new migrations
docker-compose exec backend alembic upgrade head
```

---

## Troubleshooting

### LLM Service Not Starting

**Symptoms**: `llm-service` container exits immediately

**Check**:
```bash
# View logs
docker-compose logs llm-service

# Common issues:
# 1. Insufficient GPU memory
nvidia-smi  # Check VRAM availability

# 2. Model files not found
docker-compose exec llm-service ls -la /models

# 3. CUDA driver version mismatch
nvidia-smi  # Check CUDA version
```

**Solutions**:
- Reduce `gpu_memory_utilization` in config
- Verify model files were correctly copied
- Update NVIDIA drivers

### Backend API Errors

**Symptoms**: 500 errors on API requests

**Check**:
```bash
# View backend logs
docker-compose logs backend

# Check database connection
docker-compose exec backend python -c "from app.core.database import engine; engine.connect()"

# Check environment variables
docker-compose exec backend env | grep -E '(POSTGRES|SECRET_KEY)'
```

### Frontend Not Loading

**Symptoms**: Blank page or connection errors

**Check**:
```bash
# View frontend logs
docker-compose logs frontend

# Check if backend is reachable
docker-compose exec frontend curl http://backend:8000/api/v1/health

# Verify API URL in environment
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL
```

### Database Connection Issues

**Symptoms**: Backend can't connect to database

**Check**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection manually
docker-compose exec backend python -c "import psycopg2; psycopg2.connect('postgresql://llm_app:<password>@postgres:5432/llm_webapp')"
```

### Slow LLM Responses

**Symptoms**: Responses take >10 seconds

**Optimize**:
```bash
# Check GPU usage
nvidia-smi

# Tune vLLM parameters in .env:
# - Reduce MAX_MODEL_LEN (e.g., 2048 instead of 4096)
# - Reduce MAX_NUM_SEQS (concurrent requests)
# - Increase GPU_MEMORY_UTILIZATION (if VRAM available)

# Restart LLM service after changes
docker-compose restart llm-service
```

---

## Security Checklist

- [ ] Change default passwords (admin, database)
- [ ] Generate secure `SECRET_KEY` (64+ random characters)
- [ ] Configure firewall to restrict access to internal network
- [ ] Enable HTTPS (use reverse proxy with SSL certificate)
- [ ] Set `Secure` flag on cookies in production
- [ ] Configure session timeout (30 minutes recommended)
- [ ] Set up audit logging (track admin actions)
- [ ] Configure log rotation to prevent disk fill-up
- [ ] Set up regular database backups
- [ ] Test backup restoration procedure
- [ ] Document emergency recovery procedures
- [ ] Restrict SSH access to server (key-based auth only)

---

## Performance Tuning

### LLM Service

```yaml
# In llm-service/config.yaml
model: /models/llama-3-8b
max_model_len: 4096          # Reduce if OOM errors
max_num_seqs: 16             # Concurrent requests (adjust based on VRAM)
gpu_memory_utilization: 0.9  # Increase if VRAM available
tensor_parallel_size: 1      # Use multiple GPUs if available
```

### Database

```sql
-- Add indexes for common queries
CREATE INDEX idx_conversations_user_updated ON conversations(user_id, updated_at DESC);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at ASC);
CREATE INDEX idx_documents_user_uploaded ON documents(user_id, uploaded_at DESC);

-- Tune PostgreSQL settings (in postgresql.conf)
shared_buffers = 4GB         # 25% of RAM
effective_cache_size = 12GB  # 75% of RAM
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
```

### Frontend

```javascript
// next.config.js
module.exports = {
  output: 'standalone',  // Smaller Docker image
  compress: true,        // Enable gzip compression
  reactStrictMode: true,
  swcMinify: true,       // Faster minification
}
```

---

## Next Steps

After successful deployment:

1. **User Training**: Train employees on how to use the system
2. **Monitoring**: Set up monitoring dashboard (admin panel)
3. **Feedback Loop**: Collect user feedback on response quality
4. **Documentation**: Create internal user guide (Korean)
5. **Maintenance Plan**: Schedule regular updates and backups
6. **Scale Testing**: Test with 10+ concurrent users
7. **Disaster Recovery**: Document and test recovery procedures

---

## Support & Resources

**Documentation**:
- [spec.md](./spec.md) - Feature specification
- [plan.md](./plan.md) - Implementation plan
- [data-model.md](./data-model.md) - Database schema
- [contracts/api-spec.yaml](./contracts/api-spec.yaml) - API documentation

**Useful Commands**:
```bash
# Quick health check
docker-compose ps && docker stats --no-stream

# View all logs
docker-compose logs -f --tail=100

# Database backup
docker-compose exec postgres pg_dump -U llm_app llm_webapp | gzip > backup-$(date +%Y%m%d).sql.gz

# GPU monitoring
watch -n 1 nvidia-smi
```

**External Resources** (internet access required):
- [vLLM Documentation](https://docs.vllm.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
