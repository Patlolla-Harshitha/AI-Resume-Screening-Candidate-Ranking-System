"""
Sentence Transformer embedding service.
Implements a singleton pattern with thread-safe lazy initialization,
batch processing, and LRU caching for repeated texts.
"""

from __future__ import annotations

import threading
from functools import lru_cache
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings
from utils.logger import get_logger
from utils.text_utils import normalize_whitespace

logger = get_logger("ai.embedding_service")


class EmbeddingService:
    """
    Singleton wrapper around SentenceTransformer.

    Features:
    - Lazy model loading (only loaded when first requested)
    - Thread-safe singleton instantiation
    - Batch embedding with configurable batch size
    - LRU caching for frequently-embedded identical texts
    - Normalized embeddings (unit vectors) for cosine similarity
    """

    _instance: Optional["EmbeddingService"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Private constructor — use get_instance() instead."""
        logger.info(
            "Loading Sentence Transformer model: %s", settings.SENTENCE_TRANSFORMER_MODEL
        )
        self._model = SentenceTransformer(
            settings.SENTENCE_TRANSFORMER_MODEL,
            cache_folder=settings.MODEL_CACHE_DIR,
        )
        self._model_name = settings.SENTENCE_TRANSFORMER_MODEL
        self._embedding_dim: int = self._model.get_sentence_embedding_dimension()
        logger.info(
            "✅ Embedding model loaded — dim=%d model=%s",
            self._embedding_dim,
            self._model_name,
        )

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        """
        Return the singleton EmbeddingService instance.
        Thread-safe double-checked locking pattern.

        Returns:
            EmbeddingService: The singleton instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @property
    def embedding_dim(self) -> int:
        """Dimension of the embedding vectors produced by this model."""
        return self._embedding_dim

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate a normalized embedding for a single text string.
        The text is preprocessed (whitespace normalization, truncation) before embedding.

        Args:
            text: Input text to embed.

        Returns:
            np.ndarray: 1-D unit-vector embedding of shape (embedding_dim,).
        """
        if not text or not text.strip():
            return np.zeros(self._embedding_dim, dtype=np.float32)

        preprocessed = self._preprocess(text)
        embedding = self._model.encode(
            preprocessed,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embedding.astype(np.float32)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate normalized embeddings for a list of texts in batches.

        Args:
            texts: List of input texts.

        Returns:
            np.ndarray: 2-D array of shape (len(texts), embedding_dim).
        """
        if not texts:
            return np.zeros((0, self._embedding_dim), dtype=np.float32)

        preprocessed = [self._preprocess(t) for t in texts]

        embeddings = self._model.encode(
            preprocessed,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        logger.debug("Embedded batch of %d texts", len(texts))
        return embeddings.astype(np.float32)

    def embed_text_to_list(self, text: str) -> List[float]:
        """
        Generate embedding and return as a plain Python list.
        Useful for JSON serialization and database storage.

        Args:
            text: Input text.

        Returns:
            List[float]: Embedding as a list of floats.
        """
        return self.embed_text(text).tolist()

    @staticmethod
    def _preprocess(text: str) -> str:
        """
        Preprocess text before embedding.
        Normalizes whitespace and truncates to 512 words to avoid
        exceeding typical transformer context limits.

        Args:
            text: Raw input text.

        Returns:
            str: Preprocessed text.
        """
        text = normalize_whitespace(text)
        # Truncate to ~512 words (approximate; the tokenizer will handle exact limits)
        words = text.split()
        if len(words) > 512:
            text = " ".join(words[:512])
        return text


def get_embedding_service() -> EmbeddingService:
    """Module-level convenience function to get the embedding service singleton."""
    return EmbeddingService.get_instance()
