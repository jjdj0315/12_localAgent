"""
ML-Based Content Filter

Phase 2 filtering using toxic-bert model for toxic content detection.
Runs on CPU, supports Korean language.

Model: unitary/toxic-bert (~400MB)
"""

import os
from typing import Tuple, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MLFilter:
    """
    ML-Based Toxic Content Filter

    Uses unitary/toxic-bert for toxic content classification.
    Optimized for CPU inference in air-gapped environment.

    Categories detected:
    - Toxic
    - Severe Toxic
    - Obscene
    - Threat
    - Insult
    - Identity Hate
    """

    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.7):
        """
        Initialize ML Filter.

        Args:
            model_path: Path to local toxic-bert model (None = auto-detect)
            confidence_threshold: Minimum confidence score for detection (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.tokenizer = None
        self.model_loaded = False

        # Try to load model
        try:
            self._load_model(model_path)
        except Exception as e:
            logger.warning(f"Failed to load ML filter model: {e}")
            logger.warning("ML filtering will be disabled. Only rule-based filtering will work.")

    def _load_model(self, model_path: Optional[str] = None):
        """
        Load toxic-bert model from local storage.

        Args:
            model_path: Path to model directory

        Raises:
            ImportError: If transformers library not available
            FileNotFoundError: If model not found
        """
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
        except ImportError:
            raise ImportError(
                "transformers and torch are required for ML filtering. "
                "Install with: pip install transformers torch"
            )

        # Auto-detect model path
        if model_path is None:
            # Try multiple possible locations
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "models_storage" / "toxic-bert",
                Path(__file__).parent.parent.parent.parent / "models" / "toxic-bert",
                Path.home() / ".cache" / "huggingface" / "transformers" / "toxic-bert",
            ]

            for path in possible_paths:
                if path.exists():
                    model_path = str(path)
                    logger.info(f"Found toxic-bert model at: {model_path}")
                    break

        if model_path is None or not Path(model_path).exists():
            # Try to load from HuggingFace cache (if internet available)
            logger.warning("Local model not found. Attempting to load from HuggingFace...")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained("unitary/toxic-bert")
                self.model = AutoModelForSequenceClassification.from_pretrained("unitary/toxic-bert")
                logger.info("Successfully loaded toxic-bert from HuggingFace")
            except Exception as e:
                raise FileNotFoundError(
                    f"ML model not found. For air-gapped deployment, download toxic-bert to: "
                    f"{Path(__file__).parent.parent.parent.parent / 'models_storage' / 'toxic-bert'}\n"
                    f"Download instructions: python scripts/download_ml_models.py\n"
                    f"Error: {e}"
                )
        else:
            # Load from local path
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)
            logger.info(f"Successfully loaded toxic-bert from {model_path}")

        # Set to evaluation mode and CPU
        self.model.eval()
        self.model.to('cpu')
        self.model_loaded = True

    def check_content(self, content: str) -> Tuple[bool, float, List[str]]:
        """
        Check content for toxic content using ML model.

        Args:
            content: Text content to analyze

        Returns:
            Tuple of (is_safe, confidence, detected_categories)
            - is_safe: True if content is safe
            - confidence: Maximum confidence score across all categories
            - detected_categories: List of detected toxic categories
        """
        if not self.model_loaded:
            logger.warning("ML model not loaded. Skipping ML filtering.")
            return True, 0.0, []

        if not content or not content.strip():
            return True, 0.0, []

        try:
            import torch
            from torch.nn.functional import sigmoid

            # Tokenize
            inputs = self.tokenizer(
                content,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = sigmoid(outputs.logits)

            # toxic-bert outputs 6 categories
            # [toxic, severe_toxic, obscene, threat, insult, identity_hate]
            category_names = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

            # Get predictions above threshold
            detected_categories = []
            max_confidence = 0.0

            for i, category in enumerate(category_names):
                score = predictions[0][i].item()
                max_confidence = max(max_confidence, score)

                if score >= self.confidence_threshold:
                    detected_categories.append(category)
                    logger.info(f"Detected {category} with confidence {score:.3f}")

            is_safe = len(detected_categories) == 0

            return is_safe, max_confidence, detected_categories

        except Exception as e:
            logger.error(f"ML filter error: {e}")
            # On error, fail open (allow content)
            return True, 0.0, []

    def is_available(self) -> bool:
        """Check if ML filter is available"""
        return self.model_loaded

    def get_model_info(self) -> dict:
        """Get information about loaded model"""
        return {
            "model_loaded": self.model_loaded,
            "model_name": "unitary/toxic-bert",
            "confidence_threshold": self.confidence_threshold,
            "device": "cpu"
        }
