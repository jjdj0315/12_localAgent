#!/usr/bin/env python3
"""
Setup models directory structure for Phase 10

Creates required directories and placeholder files for GGUF models and LoRA adapters.

Usage:
    python scripts/setup_models_directory.py
"""

from pathlib import Path


def setup_models_directory(base_dir: Path = Path(".")):
    """
    Create models directory structure

    Structure:
        models/
        ├── README.md
        ├── .gitignore
        └── lora/
            └── .gitkeep
    """
    models_dir = base_dir / "models"
    lora_dir = models_dir / "lora"

    print("=" * 60)
    print("Setting up models directory structure")
    print("=" * 60)
    print()

    # Create directories
    models_dir.mkdir(parents=True, exist_ok=True)
    lora_dir.mkdir(parents=True, exist_ok=True)

    print(f"[OK] Created: {models_dir}")
    print(f"[OK] Created: {lora_dir}")

    # Create .gitkeep in lora directory
    gitkeep_path = lora_dir / ".gitkeep"
    gitkeep_path.touch()
    print(f"[OK] Created: {gitkeep_path}")

    # Create .gitignore to exclude GGUF files (large binaries)
    gitignore_path = models_dir / ".gitignore"
    gitignore_content = """# Exclude large GGUF model files
*.gguf

# Exclude other model formats
*.bin
*.safetensors

# Keep directory structure
!.gitkeep
!README.md
"""
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print(f"[OK] Created: {gitignore_path}")

    # Create README
    readme_path = models_dir / "README.md"
    readme_content = """# Models Directory

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
"""
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"[OK] Created: {readme_path}")

    print()
    print("=" * 60)
    print("Models directory setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Download GGUF model: python scripts/download_gguf_model.py")
    print("  2. (Optional) Create dummy LoRA: python scripts/create_dummy_lora.py")
    print("  3. Configure .env with model paths")


if __name__ == "__main__":
    setup_models_directory()
