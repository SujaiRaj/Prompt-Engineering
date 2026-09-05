"""Shows cache validation against the highest document version currently in the corpus."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
from app.cache import CACHE_FILE, clear, lookup
from app.config import CACHE_DIR
from app.embeddings import embed

clear()
question = "How many annual leave days do employees receive?"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE.write_text(json.dumps([{"question": question, "embedding": embed([question])[0], "answer": "MOCK MODE: 20 days", "citations": [], "document_versions": {"Employee Leave Policy": "1"}, "mode": "mock", "timestamp": "demo"}]))
entry, _ = lookup(question)
print("Cached v1 answer (20 days) after active policy becomes v2 (24 days):", "REJECTED" if entry is None else "ERROR")
print("The stale v1 cache entry was removed before it could be served.")
