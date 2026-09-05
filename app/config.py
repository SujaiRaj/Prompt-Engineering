from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

def setting(name: str, default: str) -> str:
    return os.getenv(name, default)

MODEL_MODE = setting("MODEL_MODE", "mock").lower()
LLAMA_BASE_URL = setting("LLAMA_BASE_URL", "http://localhost:11434/v1")
LLAMA_MODEL = setting("LLAMA_MODEL", "llama3.1:8b")
GEMINI_API_KEY = setting("GEMINI_API_KEY", "")
GEMINI_MODEL = setting("GEMINI_MODEL", "gemini-2.0-flash")
EMBEDDING_MODEL = setting("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(setting("TOP_K", "3"))
CHUNK_SIZE = int(setting("CHUNK_SIZE", "400"))
CHUNK_OVERLAP = int(setting("CHUNK_OVERLAP", "60"))
CACHE_THRESHOLD = float(setting("SEMANTIC_CACHE_THRESHOLD", "0.88"))
DATA_DIR = ROOT / "data" / "hr_documents"
STORE_DIR = ROOT / "vectorstore"
CACHE_DIR = ROOT / "cache"
EXPERIMENTS_DIR = ROOT / "experiments"
