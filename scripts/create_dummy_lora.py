#!/usr/bin/env python3
"""
Create dummy LoRA adapters for Phase 10 infrastructure testing

Creates placeholder GGUF LoRA files to test LoRA loading mechanism.
These are NOT actual fine-tuned adapters - just empty files for testing.

Actual fine-tuned LoRA adapters will replace these in later phases.

Usage:
    python scripts/create_dummy_lora.py
    python scripts/create_dummy_lora.py --models-dir /custom/path/models
"""

import argparse
from pathlib import Path


# Agent names for LoRA adapters
AGENT_NAMES = [
    "citizen_support",    # 민원 지원 에이전트
    "document_writing",   # 문서 작성 에이전트
    "legal_research",     # 법규 검색 에이전트
    "data_analysis",      # 데이터 분석 에이전트
    "review",             # 검토 에이전트
]


def create_dummy_lora_files(lora_dir: Path):
    """
    Create dummy LoRA adapter files for infrastructure testing

    Args:
        lora_dir: Directory to save dummy LoRA files
    """
    # Create LoRA directory
    lora_dir.mkdir(parents=True, exist_ok=True)

    print("Creating dummy LoRA adapter files...")
    print(f"Output directory: {lora_dir}")
    print()

    # Create dummy file for each agent
    for agent_name in AGENT_NAMES:
        filename = f"{agent_name}_dummy.gguf"
        filepath = lora_dir / filename

        # Create empty file (or minimal placeholder)
        with open(filepath, 'wb') as f:
            # Write minimal GGUF header (placeholder)
            # Real GGUF files have specific binary structure
            # This is just for testing file detection
            dummy_content = b'GGUF_DUMMY_LORA'
            f.write(dummy_content)

        print(f"  ✓ Created: {filepath} ({len(dummy_content)} bytes)")

    print()
    print("=" * 60)
    print("Dummy LoRA adapters created successfully!")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT:")
    print("   These are DUMMY files for infrastructure testing only.")
    print("   They do NOT contain actual fine-tuned weights.")
    print()
    print("To use LoRA adapters:")
    print("  1. Set ENABLE_LORA=true in .env")
    print(f"  2. Set LORA_ADAPTERS_PATH={lora_dir} in .env")
    print("  3. LlamaCppLLMService will detect these files")
    print()
    print("To replace with real LoRA adapters:")
    print("  1. Fine-tune adapters using LoRA training script")
    print(f"  2. Save GGUF LoRA files to {lora_dir}")
    print("  3. Replace dummy files with real adapter files")
    print()
    print("Files created:")
    for agent_name in AGENT_NAMES:
        filename = f"{agent_name}_dummy.gguf"
        print(f"  - {lora_dir / filename}")


def create_readme(lora_dir: Path):
    """Create README in LoRA directory"""
    readme_path = lora_dir / "README.md"

    readme_content = """# LoRA Adapters Directory

This directory contains LoRA adapter files for agent-specific fine-tuning.

## Current Status

**Phase 10 (Now)**: Dummy files for infrastructure testing
- Files ending with `_dummy.gguf` are placeholders
- Used to test LoRA loading mechanism
- Do NOT contain actual fine-tuned weights

**Later Phases**: Replace with real fine-tuned adapters
- Train LoRA adapters using task-specific datasets
- Export to GGUF format
- Replace dummy files with real adapter files

## Agent LoRA Adapters

- `citizen_support_dummy.gguf` - 민원 지원 (Citizen Support)
- `document_writing_dummy.gguf` - 문서 작성 (Document Writing)
- `legal_research_dummy.gguf` - 법규 검색 (Legal Research)
- `data_analysis_dummy.gguf` - 데이터 분석 (Data Analysis)
- `review_dummy.gguf` - 검토 (Review)

## Environment Configuration

```bash
# .env
ENABLE_LORA=true
LORA_ADAPTERS_PATH=/models/lora
```

## Fine-Tuning Workflow (Later)

1. Collect task-specific datasets
2. Fine-tune using LoRA training script
3. Export to GGUF format
4. Replace dummy files in this directory
5. Restart backend service

## Notes

- LoRA adapters are optional
- System works with prompts alone
- LoRA improves performance for specialized tasks
- Each adapter is typically 50-200MB
"""

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"  ✓ Created README: {readme_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Create dummy LoRA adapters for Phase 10 testing"
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path("models"),
        help="Models directory (LoRA files saved to models/lora)"
    )

    args = parser.parse_args()
    lora_dir = args.models_dir / "lora"

    print("=" * 60)
    print("Dummy LoRA Adapter Generator - Phase 10 Testing")
    print("=" * 60)
    print()

    create_dummy_lora_files(lora_dir)
    create_readme(lora_dir)


if __name__ == "__main__":
    main()
