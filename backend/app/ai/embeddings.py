"""Image embedding generator using SentenceTransformers CLIP (clip-ViT-B-32) with fallback vector generator."""

import base64
import hashlib
import io
import logging
import math
import os
from typing import Any, List, Union

logger = logging.getLogger(__name__)


class ImageEmbedder:
    """Generates 512-dimensional L2-normalized image feature embeddings for similarity matching."""

    EMBEDDING_DIM = 512

    def __init__(self, model_name: str = "clip-ViT-B-32"):
        self.model_name = model_name
        self._model = None
        self._model_failed = False

    def _load_model(self) -> Any:
        """Lazily load SentenceTransformer model if available."""
        if self._model is not None:
            return self._model
        if self._model_failed:
            return None

        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer model '%s'...", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            return self._model
        except Exception as err:
            logger.warning("Could not load SentenceTransformer model '%s': %s. Using fallback vector generator.", self.model_name, err)
            self._model_failed = True
            return None

    def generate_embedding(self, image_data: Union[bytes, str, Any]) -> List[float]:
        """Generate a 512-dim normalized float vector from raw bytes, base64, file path, or PIL Image.

        Args:
            image_data: Raw byte array, base64 data string, file path, or PIL Image instance.

        Returns:
            List of 512 float values normalized such that L2 norm == 1.0.
        """
        raw_bytes = self._extract_bytes(image_data)
        model = self._load_model()

        if model is not None:
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                vec = model.encode(img)
                # Convert to Python float list and normalize
                float_vec = [float(x) for x in vec]
                return self.normalize(float_vec)
            except Exception as err:
                logger.error("Failed to generate embedding with SentenceTransformers model: %s. Using fallback.", err)

        return self._generate_fallback_embedding(raw_bytes)

    def _extract_bytes(self, image_data: Union[bytes, str, Any]) -> bytes:
        """Extract raw bytes from various possible input formats."""
        if isinstance(image_data, bytes):
            return image_data
        elif isinstance(image_data, str):
            if image_data.startswith("data:image"):
                _, encoded = image_data.split(",", 1)
                return base64.b64decode(encoded)
            elif os.path.exists(image_data):
                with open(image_data, "rb") as f:
                    return f.read()
            else:
                try:
                    return base64.b64decode(image_data)
                except Exception:
                    return image_data.encode("utf-8")
        else:
            # Handle PIL Image or other object
            try:
                buf = io.BytesIO()
                image_data.save(buf, format="JPEG")
                return buf.getvalue()
            except Exception:
                return str(image_data).encode("utf-8")

    def _generate_fallback_embedding(self, raw_bytes: bytes) -> List[float]:
        """Generate a deterministic 512-dim normalized vector using cryptographic hash expansion."""
        vec: List[float] = []
        seed_hash = raw_bytes
        
        while len(vec) < self.EMBEDDING_DIM:
            digest = hashlib.sha512(seed_hash).digest()
            # Convert pairs of bytes into floats in [-1.0, 1.0]
            for i in range(0, len(digest) - 1, 2):
                val = (digest[i] * 256 + digest[i + 1]) / 65535.0
                vec.append(val * 2.0 - 1.0)
                if len(vec) == self.EMBEDDING_DIM:
                    break
            seed_hash = digest

        return self.normalize(vec)

    @staticmethod
    def normalize(vec: List[float]) -> List[float]:
        """Normalize vector to unit length (L2 norm = 1.0)."""
        squared_sum = sum(x * x for x in vec)
        norm = math.sqrt(squared_sum)
        if norm == 0.0:
            return [0.0] * len(vec)
        return [x / norm for x in vec]

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity score between two normalized embedding vectors (returns -1.0 to 1.0)."""
        if len(vec1) != len(vec2) or not vec1 or not vec2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        
        sim = dot_product / (norm1 * norm2)
        # Clamp value to [-1.0, 1.0] due to float precision
        return max(-1.0, min(1.0, float(sim)))
