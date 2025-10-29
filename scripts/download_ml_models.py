#!/usr/bin/env python3
"""
Download ML Models for Air-Gapped Deployment

This script downloads required ML models for safety filtering:
- unitary/toxic-bert (~400MB)

Run this script with internet access, then copy models_storage/ to air-gapped server.
"""

import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def download_toxic_bert(output_dir: Path):
    """Download unitary/toxic-bert model"""
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
    except ImportError:
        logger.error("transformers library not found. Install with: pip install transformers")
        sys.exit(1)

    logger.info("Downloading unitary/toxic-bert model...")
    logger.info(f"Output directory: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Download tokenizer
        logger.info("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("unitary/toxic-bert")
        tokenizer.save_pretrained(output_dir)

        # Download model
        logger.info("Downloading model...")
        model = AutoModelForSequenceClassification.from_pretrained("unitary/toxic-bert")
        model.save_pretrained(output_dir)

        logger.info(f"✓ Successfully downloaded toxic-bert to {output_dir}")
        logger.info(f"  Model size: ~400MB")

        # Test loading
        logger.info("Testing model loading...")
        test_tokenizer = AutoTokenizer.from_pretrained(output_dir, local_files_only=True)
        test_model = AutoModelForSequenceClassification.from_pretrained(output_dir, local_files_only=True)
        logger.info("✓ Model loads successfully")

        return True

    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return False


def main():
    # Determine output directory
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "models_storage"

    logger.info("=" * 60)
    logger.info("ML Model Downloader for Safety Filtering")
    logger.info("=" * 60)
    logger.info(f"Project root: {project_root}")
    logger.info(f"Models will be saved to: {models_dir}")
    logger.info("")

    # Download toxic-bert
    toxic_bert_dir = models_dir / "toxic-bert"
    success = download_toxic_bert(toxic_bert_dir)

    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.info("✓ All models downloaded successfully!")
        logger.info("")
        logger.info("For air-gapped deployment:")
        logger.info(f"1. Copy the entire 'models_storage/' directory to your air-gapped server")
        logger.info(f"2. Place it in the backend root directory")
        logger.info(f"3. The Safety Filter will auto-detect and load models")
    else:
        logger.error("✗ Model download failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
