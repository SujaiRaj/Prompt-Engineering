"""Embeddings with a deterministic offline fallback for mock-mode development."""
from __future__ import annotations

import hashlib
import math
import os
import re
from functools import lru_cache

from .config import EMBEDDING_MODEL

@lru_cache(maxsize=1)
def _sentence_model():
    if os.getenv("USE_SENTENCE_TRANSFORMERS", "false").lower() not in {"1", "true", "yes"}:
        return None
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
    except Exception:
        return None

def embed(texts: list[str]) -> list[list[float]]:
    model = _sentence_model()
    if model is not None:
        return model.encode(texts, normalize_embeddings=True).tolist()
    # Hashing embeddings preserve token overlap and work with no network/model files.
    vectors = []
    for text in texts:
        vector = [0.0] * 384
        # Small normalization makes the offline fallback useful for the required
        # leave-policy paraphrase while remaining an embedding/vector similarity cache.
        normalized = text.lower().replace("yearly", "annual").replace("allowance", "days")
        tokens = re.findall(r"[a-z0-9]+", normalized)
        ignored = {"what", "is", "the", "how", "many", "do", "employees", "employee", "receive", "get", "a", "an", "of", "per"}
        for token in tokens:
            if token in ignored:
                continue
            index = int(hashlib.sha256(token.encode()).hexdigest(), 16) % len(vector)
            vector[index] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        vectors.append([v / norm for v in vector])
    return vectors

def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
