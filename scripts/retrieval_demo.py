import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.rag import ingest, retrieve

ingest()
for item in retrieve("How many annual leave days do employees receive?"):
    print(f"[Source: {item['metadata']['title']}, Section {item['metadata']['section']}]\n{item['text']}\n")
