# Offline Dependency Bundling Guide

## Purpose

This script creates a complete offline bundle of all dependencies required for the Local LLM Web Application, enabling deployment in air-gapped (closed network) environments without internet access.

## Prerequisites

**Run this script on a machine WITH internet access**, then transfer the generated bundle to the air-gapped target server.

### Required Tools

- Python 3.11+
- `pip` package manager
- `huggingface-cli` (install via `pip install huggingface-hub`)
- `tar` and `gzip` utilities (standard on Linux/macOS, available via Git Bash on Windows)
- Sufficient disk space (~10GB for all models and packages)

### Hugging Face Authentication

Some models may require authentication. Run this before executing the script:

```bash
huggingface-cli login
```

Enter your Hugging Face access token when prompted.

## Usage

### 1. Create Offline Bundle (Internet-connected machine)

```bash
cd /path/to/12_localAgent
chmod +x scripts/bundle-offline-deps.sh
./scripts/bundle-offline-deps.sh
```

**Expected output:**
- Python packages downloaded to `offline_packages/python_packages/`
- AI models downloaded to `offline_packages/models/`
- Tarball archive created: `local-llm-webapp-offline-bundle_YYYYMMDD_HHMMSS.tar.gz`

**Time estimate:** 15-30 minutes depending on internet speed

**Disk space required:**
- Temporary: ~8GB (for downloads)
- Final archive: ~6GB (compressed)

### 2. Transfer Bundle to Air-Gapped Server

Use USB drive, secure file transfer, or approved method:

```bash
# Example: Copy to USB
cp local-llm-webapp-offline-bundle_*.tar.gz /mnt/usb/

# Example: Secure copy (if network transfer allowed)
scp local-llm-webapp-offline-bundle_*.tar.gz user@airgapped-server:/opt/deployment/
```

### 3. Install on Air-Gapped Server

#### Step 3.1: Extract Bundle

```bash
cd /opt/deployment  # or your target directory
tar -xzf local-llm-webapp-offline-bundle_*.tar.gz
```

This creates the following structure:
```
/opt/deployment/
├── python_packages/       # All pip packages (.whl, .tar.gz)
├── models/
│   ├── qwen-gguf/        # GGUF model for Phase 10 (llama.cpp)
│   ├── qwen-safetensors/ # Safetensors for Phase 13 (vLLM, optional)
│   ├── toxic-bert/       # Safety filter model
│   └── sentence-transformers/  # Embedding model for tags
```

#### Step 3.2: Install Python Dependencies

```bash
# Navigate to project root
cd /path/to/12_localAgent

# Install from offline packages
pip install --no-index --find-links=/opt/deployment/python_packages -r backend/requirements.txt
```

**Verification:**
```bash
pip list | grep -E "fastapi|sqlalchemy|transformers|llama-cpp-python"
```

#### Step 3.3: Setup Model Files

```bash
# Create models directory structure
mkdir -p backend/models/lora

# Copy base model (GGUF for Phase 10)
cp /opt/deployment/models/qwen-gguf/qwen2.5-1.5b-instruct-q4_k_m.gguf backend/models/

# Copy safety filter model
cp -r /opt/deployment/models/toxic-bert backend/models/

# Copy embedding model
cp -r /opt/deployment/models/sentence-transformers backend/models/

# (Optional) Copy vLLM model for Phase 13
cp -r /opt/deployment/models/qwen-safetensors backend/models/qwen-vllm
```

**Verification:**
```bash
ls -lh backend/models/
# Expected: qwen2.5-1.5b-instruct-q4_k_m.gguf (~1.5GB)
# Expected: toxic-bert/ directory
# Expected: sentence-transformers/ directory
```

#### Step 3.4: Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit configuration
nano backend/.env
```

Set the following variables:
```bash
# LLM Backend (Phase 10: llama.cpp, Phase 13: vLLM)
LLM_BACKEND=llama_cpp

# Model paths
GGUF_MODEL_PATH=/path/to/backend/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
TOXIC_BERT_PATH=/path/to/backend/models/toxic-bert
SENTENCE_TRANSFORMERS_PATH=/path/to/backend/models/sentence-transformers
```

#### Step 3.5: Verify Installation

```bash
# Test model loading
python backend/test_llama_load.py

# Expected output: "Model loaded successfully"
```

## Troubleshooting

### Issue: `huggingface-cli` not found

**Solution:**
```bash
pip install huggingface-hub
```

### Issue: "Authentication required" error

**Solution:**
```bash
huggingface-cli login
# Enter your Hugging Face token from https://huggingface.co/settings/tokens
```

### Issue: Disk space error during download

**Solution:**
- Free up disk space (models require ~8GB temporary storage)
- Use external drive: `OUTPUT_DIR=/mnt/external ./scripts/bundle-offline-deps.sh`

### Issue: Model files corrupted after transfer

**Solution:**
```bash
# Verify archive integrity before transfer
sha256sum local-llm-webapp-offline-bundle_*.tar.gz > bundle.sha256

# After transfer, verify:
sha256sum -c bundle.sha256
```

### Issue: pip install fails with "No matching distribution"

**Solution:**
- Ensure Python version matches (3.11+)
- Check architecture compatibility (x86_64 vs ARM)
- Re-run bundle script on compatible machine

## Bundle Contents

### Python Packages (~500MB)

| Package Category | Key Packages | Size |
|-----------------|--------------|------|
| Web Framework | fastapi, uvicorn, pydantic | ~50MB |
| Database | sqlalchemy, alembic, psycopg2 | ~30MB |
| LLM | llama-cpp-python, transformers, torch | ~300MB |
| ML/NLP | sentence-transformers, bitsandbytes | ~80MB |
| Utilities | python-docx, pdfplumber, chromadb | ~40MB |

### AI Models (~6GB)

| Model | Purpose | Size | Phase |
|-------|---------|------|-------|
| Qwen2.5-1.5B GGUF | Base LLM (CPU) | ~1.5GB | 10 (llama.cpp) |
| Qwen2.5-1.5B Safetensors | Base LLM (GPU) | ~2GB | 13 (vLLM, optional) |
| Toxic-BERT | Safety filtering | ~400MB | 8 (Safety Filter) |
| Sentence-Transformers | Tag matching, embeddings | ~200MB | 4 (Tags) |

## Update Procedure

To update the bundle with new dependencies:

1. Update `backend/requirements.txt` with new packages
2. Re-run `./scripts/bundle-offline-deps.sh`
3. New bundle will include updated packages
4. Transfer and install on air-gapped server as described above

## Security Notes

- **Model Verification**: Models are downloaded from official Hugging Face repositories
- **Package Integrity**: pip verifies package signatures during installation
- **Archive Integrity**: Use SHA256 checksums to verify bundle integrity after transfer
- **Access Control**: Restrict access to bundle files (contains proprietary models)

## Support

For issues or questions:
- Check backend logs: `tail -f backend/logs/app.log`
- Review constitution: `.specify/memory/constitution.md` (Air-Gap Compatibility principle)
- Contact: IT support team

---

**Version**: 1.0.0
**Last Updated**: 2025-01-30
**Maintained By**: 12_localAgent Development Team
