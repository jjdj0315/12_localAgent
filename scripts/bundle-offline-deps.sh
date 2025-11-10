#!/bin/bash
# Offline Dependency Bundling Script for Air-Gapped Deployment
# This script downloads all required dependencies for the Local LLM Web Application
# to enable installation in closed network environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_ROOT/offline_packages"
MODELS_DIR="$OUTPUT_DIR/models"

echo "=========================================="
echo "Local LLM Web App - Offline Bundle Creator"
echo "=========================================="
echo ""

# Create output directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$MODELS_DIR"
mkdir -p "$OUTPUT_DIR/python_packages"

echo "Step 1: Downloading Python dependencies..."
echo "-------------------------------------------"
if [ -f "$PROJECT_ROOT/backend/requirements.txt" ]; then
    pip download -d "$OUTPUT_DIR/python_packages" -r "$PROJECT_ROOT/backend/requirements.txt"
    echo "✓ Python packages downloaded to $OUTPUT_DIR/python_packages"
else
    echo "ERROR: backend/requirements.txt not found"
    exit 1
fi

echo ""
echo "Step 2: Downloading HuggingFace models..."
echo "-------------------------------------------"

# Download Qwen2.5-1.5B-Instruct GGUF (for Phase 10 - llama.cpp)
echo "Downloading Qwen2.5-1.5B-Instruct GGUF Q4_K_M (Phase 10 - llama.cpp)..."
huggingface-cli download TheBloke/Qwen2.5-1.5B-Instruct-GGUF \
    qwen2.5-1.5b-instruct-q4_k_m.gguf \
    --local-dir "$MODELS_DIR/qwen-gguf" \
    --local-dir-use-symlinks False
echo "✓ GGUF model downloaded"

# Download Qwen2.5-1.5B-Instruct safetensors (optional for Phase 13 - vLLM)
echo "Downloading Qwen/Qwen2.5-1.5B-Instruct safetensors (Phase 13 - vLLM, optional)..."
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct \
    --local-dir "$MODELS_DIR/qwen-safetensors" \
    --local-dir-use-symlinks False \
    --exclude "*.bin" \
    --exclude "*.h5"
echo "✓ Safetensors model downloaded"

# Download toxic-bert for Safety Filter
echo "Downloading unitary/toxic-bert for safety filtering..."
huggingface-cli download unitary/toxic-bert \
    --local-dir "$MODELS_DIR/toxic-bert" \
    --local-dir-use-symlinks False
echo "✓ Toxic-bert model downloaded"

# Download sentence-transformers for tag matching and embeddings
echo "Downloading sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2..."
huggingface-cli download sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
    --local-dir "$MODELS_DIR/sentence-transformers" \
    --local-dir-use-symlinks False
echo "✓ Sentence-transformers model downloaded"

echo ""
echo "Step 3: Creating tarball archive..."
echo "-------------------------------------------"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="local-llm-webapp-offline-bundle_${TIMESTAMP}.tar.gz"

cd "$PROJECT_ROOT"
tar -czf "$ARCHIVE_NAME" \
    -C offline_packages . \
    2>/dev/null

if [ -f "$ARCHIVE_NAME" ]; then
    ARCHIVE_SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)
    echo "✓ Archive created: $ARCHIVE_NAME ($ARCHIVE_SIZE)"
    echo ""
    echo "=========================================="
    echo "Bundle creation completed successfully!"
    echo "=========================================="
    echo ""
    echo "Archive location: $PROJECT_ROOT/$ARCHIVE_NAME"
    echo "Archive size: $ARCHIVE_SIZE"
    echo ""
    echo "To install on air-gapped server:"
    echo "1. Transfer $ARCHIVE_NAME to the target server"
    echo "2. Extract: tar -xzf $ARCHIVE_NAME"
    echo "3. Install Python packages: pip install --no-index --find-links=python_packages -r backend/requirements.txt"
    echo "4. Copy models to: backend/models/"
    echo ""
    echo "See scripts/bundle-offline-deps.README.md for detailed instructions"
else
    echo "ERROR: Failed to create archive"
    exit 1
fi
