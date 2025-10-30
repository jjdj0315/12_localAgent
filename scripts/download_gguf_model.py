#!/usr/bin/env python3
"""
Download GGUF model for Phase 10 local testing

Downloads Qwen2.5-3B-Instruct GGUF (Q4_K_M quantization) from HuggingFace.
This model is CPU-optimized for local testing with llama-cpp-python.
3B model provides better Korean language quality than 1.5B with reasonable speed.

Usage:
    python scripts/download_gguf_model.py
    python scripts/download_gguf_model.py --model-dir /custom/path/models
    python scripts/download_gguf_model.py --quantization Q5_K_M
"""

import argparse
import sys
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("Error: huggingface_hub not installed")
    print("Install with: pip install huggingface-hub")
    sys.exit(1)


# Model configuration
DEFAULT_REPO_ID = "Qwen/Qwen2.5-3B-Instruct-GGUF"
DEFAULT_QUANTIZATION = "Q4_K_M"

QUANTIZATION_OPTIONS = {
    "Q4_K_M": "qwen2.5-3b-instruct-q4_k_m.gguf",  # Recommended (2GB, balanced)
    "Q5_K_M": "qwen2.5-3b-instruct-q5_k_m.gguf",  # Higher quality (2.5GB)
    "Q3_K_M": "qwen2.5-3b-instruct-q3_k_m.gguf",  # Smaller size (1.5GB)
    "Q8_0": "qwen2.5-3b-instruct-q8_0.gguf",      # Highest quality (3.5GB)
}


def download_gguf_model(
    model_dir: Path,
    repo_id: str = DEFAULT_REPO_ID,
    quantization: str = DEFAULT_QUANTIZATION
):
    """
    Download GGUF model from HuggingFace

    Args:
        model_dir: Directory to save model
        repo_id: HuggingFace repository ID
        quantization: Quantization level (Q4_K_M, Q5_K_M, etc.)
    """
    # Get filename for quantization
    if quantization not in QUANTIZATION_OPTIONS:
        print(f"Error: Invalid quantization '{quantization}'")
        print(f"Available options: {', '.join(QUANTIZATION_OPTIONS.keys())}")
        sys.exit(1)

    filename = QUANTIZATION_OPTIONS[quantization]

    # Create model directory
    model_dir.mkdir(parents=True, exist_ok=True)
    output_path = model_dir / filename

    # Check if already downloaded
    if output_path.exists():
        print(f"[OK] Model already exists: {output_path}")
        print(f"  File size: {output_path.stat().st_size / (1024**3):.2f} GB")
        response = input("Re-download? (y/N): ")
        if response.lower() != 'y':
            print("Skipping download")
            return

    # Download from HuggingFace
    print(f"Downloading GGUF model from HuggingFace...")
    print(f"  Repository: {repo_id}")
    print(f"  Quantization: {quantization}")
    print(f"  Filename: {filename}")
    print(f"  Destination: {output_path}")
    print()

    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=model_dir,
            local_dir_use_symlinks=False,  # Copy file instead of symlink
        )

        print()
        print(f"[OK] Download complete!")
        print(f"  Model saved to: {downloaded_path}")
        print(f"  File size: {Path(downloaded_path).stat().st_size / (1024**3):.2f} GB")
        print()
        print("Next steps:")
        print(f"  1. Set GGUF_MODEL_PATH={downloaded_path} in .env")
        print(f"  2. Set LLM_BACKEND=llama_cpp in .env")
        print(f"  3. Start backend: cd backend && uvicorn app.main:app")

    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Download GGUF model for Phase 10 local testing"
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models"),
        help="Directory to save model (default: ./models)"
    )
    parser.add_argument(
        "--repo-id",
        type=str,
        default=DEFAULT_REPO_ID,
        help=f"HuggingFace repository ID (default: {DEFAULT_REPO_ID})"
    )
    parser.add_argument(
        "--quantization",
        type=str,
        default=DEFAULT_QUANTIZATION,
        choices=list(QUANTIZATION_OPTIONS.keys()),
        help=f"Quantization level (default: {DEFAULT_QUANTIZATION})"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("GGUF Model Downloader - Phase 10 Local Testing")
    print("=" * 60)
    print()

    download_gguf_model(
        model_dir=args.model_dir,
        repo_id=args.repo_id,
        quantization=args.quantization
    )


if __name__ == "__main__":
    main()
