import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cache import clear
from app.service import ask

clear()
for question in ["What is the annual leave allowance?", "How many yearly leave days do employees receive?", "Can unused leave be carried forward?"]:
    result = ask(question, "mock")
    print(question, "=>", "HIT" if result["cache_hit"] else "MISS", f"({result['similarity']:.3f})")
