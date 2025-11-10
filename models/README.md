# Models Directory

This directory contains GGUF models and LoRA adapters for Phase 10 local testing.

## Directory Structure

```
models/
├── qwen2.5-1.5b-instruct-q4_k_m.gguf  # Base GGUF model (download required)
└── lora/                               # LoRA adapters directory
    ├── citizen_support_dummy.gguf     # Dummy adapter for testing
    ├── document_writing_dummy.gguf
    ├── legal_research_dummy.gguf
    ├── data_analysis_dummy.gguf
    └── review_dummy.gguf
```

## Setup Instructions

### 1. Download Base GGUF Model

```bash
python scripts/download_gguf_model.py
```

This downloads Qwen2.5-1.5B-Instruct Q4_K_M quantized model (~2.5GB).

### 2. Create Dummy LoRA Adapters (Optional)

```bash
python scripts/create_dummy_lora.py
```

Creates placeholder LoRA files for infrastructure testing.

### 3. Configure Environment

Add to `.env`:
```bash
GGUF_MODEL_PATH=C:/02_practice/12_localAgent/models/qwen2.5-1.5b-instruct-q4_k_m.gguf
ENABLE_LORA=false  # Set to 'true' to test LoRA loading
LORA_ADAPTERS_PATH=C:/02_practice/12_localAgent/models/lora
```

## Model Files (Not Committed)

GGUF files are excluded from git due to size (2-4GB each).
Download locally using the provided script.

## LoRA Adapters

### Phase 10 (Current)
- Dummy files for testing LoRA loading mechanism
- Files are placeholders, not actual fine-tuned weights

### Later Phases
- Replace with real fine-tuned LoRA adapters
- Train using task-specific datasets
- Export to GGUF format

## Disk Space Requirements

- Base model (Q4_K_M): ~2.5 GB
- Base model (Q5_K_M): ~3 GB
- LoRA adapters: ~50-200 MB each
- Total: ~3-4 GB minimum
