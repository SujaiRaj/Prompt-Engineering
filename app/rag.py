from __future__ import annotations

import json
import re
from pathlib import Path

from .config import CHUNK_SIZE, DATA_DIR, STORE_DIR, TOP_K
from .embeddings import cosine, embed

STORE_FILE = STORE_DIR / "chunks.json"

def _parse_document(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"---\s*\n(.*?)\n---\s*\n(.*)", raw, re.S)
    if not match:
        raise ValueError(f"Missing frontmatter: {path}")
    metadata = dict(re.findall(r"^(\w+):\s*[\"']?([^\n\"']+)[\"']?\s*$", match.group(1), re.M))
    return metadata, match.group(2).strip()

def _sections(body: str):
    matches = list(re.finditer(r"^##\s+(\d+\.\d+)\s+(.+)$", body, re.M))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        yield match.group(1), match.group(2).strip(), body[match.end():end].strip()

def ingest(documents_dir: Path = DATA_DIR) -> int:
    chunks = []
    # A versioned policy pair lives in the repository for the stale-cache demo,
    # but only the highest version is part of the active knowledge base.
    active: dict[str, tuple[dict, str, Path]] = {}
    for path in sorted(documents_dir.glob("*.md")):
        meta, body = _parse_document(path)
        title = meta["title"]
        if title not in active or int(meta.get("version", "1")) > int(active[title][0].get("version", "1")):
            active[title] = (meta, body, path)
    for meta, body, path in active.values():
        for section, heading, text in _sections(body):
            # Documents are deliberately short; section boundaries yield clean citations.
            for start in range(0, max(len(text), 1), CHUNK_SIZE):
                piece = text[start:start + CHUNK_SIZE].strip()
                if piece:
                    chunks.append({"text": piece, "metadata": {**meta, "section": section, "heading": heading, "file": path.name}})
    for item, vector in zip(chunks, embed([c["text"] for c in chunks])):
        item["embedding"] = vector
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    STORE_FILE.write_text(json.dumps(chunks, indent=2), encoding="utf-8")
    # Chroma is the normal persistent vector store when installed. The JSON copy
    # is an intentional offline fallback so mock development needs no extra runtime.
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(STORE_DIR / "chroma"))
        try:
            client.delete_collection("hr_documents")
        except Exception:
            pass
        collection = client.create_collection("hr_documents", metadata={"hnsw:space": "cosine"})
        collection.add(
            ids=[f"chunk-{i}" for i in range(len(chunks))],
            documents=[item["text"] for item in chunks],
            embeddings=[item["embedding"] for item in chunks],
            metadatas=[{k: str(v) for k, v in item["metadata"].items()} for item in chunks],
        )
    except Exception:
        pass
    return len(chunks)

def _load() -> list[dict]:
    if not STORE_FILE.exists():
        ingest()
    return json.loads(STORE_FILE.read_text(encoding="utf-8"))

def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    query = embed([question])[0]
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(STORE_DIR / "chroma"))
        collection = client.get_collection("hr_documents")
        result = collection.query(query_embeddings=[query], n_results=top_k, include=["documents", "metadatas", "distances"])
        return [{"text": text, "metadata": meta, "score": 1 - distance}
                for text, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])]
    except Exception:
        pass
    scored = []
    for item in _load():
        copy = {"text": item["text"], "metadata": item["metadata"], "score": cosine(query, item["embedding"])}
        scored.append(copy)
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]

def current_versions() -> dict[str, str]:
    """Current corpus versions, derived from the documents rather than cache state."""
    result = {}
    for path in DATA_DIR.glob("*.md"):
        meta, _ = _parse_document(path)
        title, version = meta["title"], meta.get("version", "1")
        if title not in result or int(version) > int(result[title]):
            result[title] = version
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        print(f"Ingested {ingest()} chunks into {STORE_DIR}")
    else:
        for chunk in retrieve("How many annual leave days do employees receive?"):
            print(f"{chunk['metadata']['title']} §{chunk['metadata']['section']}: {chunk['text']}")
