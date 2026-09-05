"""Runs V1/V2/V3. Use llama or gemini for report results; mock is development-only."""
import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import EXPERIMENTS_DIR
from app.llm import call_gemini, call_llama
from app.prompts import PROMPTS, build_user_prompt
from app.rag import retrieve
from app.service import _mock_answer

mode = sys.argv[1] if len(sys.argv) > 1 else "mock"
questions = ["How many annual leave days do employees receive?", "Where do I collect my laptop?", "Which expenses are reimbursable?", "What are office access hours?", "Who handles HR questions?", "Can unused leave be carried forward?", "How do I get VPN access?", "How do I get a parking permit?"]
rows = []
for question in questions:
    contexts = retrieve(question)
    for label, system in PROMPTS.items():
        if mode == "mock": answer = _mock_answer(question, contexts)
        elif mode == "llama": answer = call_llama(system, build_user_prompt(question, contexts))
        elif mode == "gemini": answer = call_gemini(system, build_user_prompt(question, contexts))
        else: raise SystemExit("Usage: python scripts/prompt_comparison.py [mock|llama|gemini]")
        rows.append({"mode": mode.upper(), "question": question, "prompt": label, "answer": answer, "answer_quality_manual": "", "citation_quality_manual": "", "hallucination_manual": ""})
EXPERIMENTS_DIR.mkdir(exist_ok=True)
with (EXPERIMENTS_DIR / f"prompt_comparison_{mode}.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
print(f"Saved {mode.upper()} prompt comparison. Mock output is not a real prompt experiment.")
