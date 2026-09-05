from __future__ import annotations

import json
from datetime import datetime, timezone

from .config import CACHE_DIR, CACHE_THRESHOLD
from .embeddings import cosine, embed
from .rag import current_versions

CACHE_FILE = CACHE_DIR / "semantic_cache.json"

def _load() -> list[dict]:
    if not CACHE_FILE.exists():
        return []
    return json.loads(CACHE_FILE.read_text(encoding="utf-8"))

def _save(entries: list[dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")

def clear() -> None:
    _save([])

def lookup(question: str) -> tuple[dict | None, float]:
    """Return a valid semantic match and its best similarity, otherwise (None, score)."""
    vector = embed([question])[0]
    versions = current_versions()
    best, best_score = None, 0.0
    valid_entries = []
    for entry in _load():
        if all(versions.get(title) == version for title, version in entry["document_versions"].items()):
            valid_entries.append(entry)
            score = cosine(vector, entry["embedding"])
            if score > best_score:
                best, best_score = entry, score
    _save(valid_entries)  # remove stale entries permanently
    return (best if best_score >= CACHE_THRESHOLD else None), best_score

def store(question: str, answer: str, citations: list[str], contexts: list[dict], mode: str) -> None:
    versions = {item["metadata"]["title"]: item["metadata"].get("version", "1") for item in contexts}
    entries = _load()
    entries.append({
        "question": question, "embedding": embed([question])[0], "answer": answer,
        "citations": citations, "document_versions": versions, "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save(entries)
