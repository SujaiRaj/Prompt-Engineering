"""Manual experiment runner. Never run with mock for final Llama/Gemini claims."""
import csv
import json
import sys
from time import perf_counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import EXPERIMENTS_DIR
from app.service import ask

mode = sys.argv[1] if len(sys.argv) > 1 else "mock"
if mode not in {"llama", "gemini", "compare", "mock"}:
    raise SystemExit("Usage: python scripts/run_experiment.py [mock|llama|gemini|compare]")
EXPERIMENTS_DIR.mkdir(exist_ok=True)
questions = json.loads((Path(__file__).resolve().parents[1] / "data" / "evaluation_questions.json").read_text())
rows = []
for question in questions:
    started = perf_counter(); result = ask(question, mode, use_cache=False); elapsed = perf_counter() - started
    rows.append({"mode": mode.upper(), "question": question, "answer": result["answer"], "citations": " | ".join(result["citations"]), "escalated": result["escalated"], "latency_seconds": round(elapsed, 3), "groundedness_manual": "", "citation_quality_manual": ""})
with (EXPERIMENTS_DIR / f"evaluation_{mode}.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
print(f"Saved {len(rows)} {mode.upper()} rows. MOCK results are development-only and must not be used for final model claims.")
