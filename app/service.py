from __future__ import annotations

import re

from . import cache
from .llm import call_gemini, call_llama
from .prompts import V3, build_user_prompt
from .rag import retrieve
from .safety import ESCALATION_MESSAGE, classify, is_sensitive

def _citations(contexts: list[dict]) -> list[str]:
    return list(dict.fromkeys(f"[Source: {x['metadata']['title']}, Section {x['metadata']['section']}]" for x in contexts))

def _mock_answer(question: str, contexts: list[dict]) -> str:
    if not contexts or contexts[0]["score"] <= 0:
        return "MOCK MODE: I could not find this information in the Northwind Retail Co. policy documents."
    primary = contexts[0]
    citation = _citations([primary])[0]
    # Deterministic development answer grounded in the highest-retrieved chunk.
    return f"MOCK MODE: {primary['text']} {citation}"

def _validate_citations(answer: str, citations: list[str]) -> str:
    # Real providers are instructed to cite; append a real retrieved citation if they omit one.
    return answer if re.search(r"\[Source: .+?, Section \d+\.\d+\]", answer) else f"{answer}\n\n{citations[0]}"

def ask(question: str, mode: str = "mock", use_cache: bool = True) -> dict:
    mode = mode.lower()
    department = classify(question)
    if is_sensitive(question):
        return {"answer": ESCALATION_MESSAGE, "citations": [], "department": department,
                "cache_hit": False, "similarity": 0.0, "escalated": True, "mode": mode}
    cached, similarity = cache.lookup(question) if use_cache else (None, 0.0)
    if cached:
        return {"answer": cached["answer"], "citations": cached["citations"], "department": department,
                "cache_hit": True, "similarity": similarity, "escalated": False, "mode": cached["mode"]}
    contexts = retrieve(question)
    citations = _citations(contexts)
    prompt = build_user_prompt(question, contexts)
    if mode == "mock":
        answer = _mock_answer(question, contexts)
    elif mode == "llama":
        answer = _validate_citations(call_llama(V3, prompt), citations)
    elif mode == "gemini":
        answer = _validate_citations(call_gemini(V3, prompt), citations)
    elif mode == "compare":
        llama = _validate_citations(call_llama(V3, prompt), citations)
        gemini = _validate_citations(call_gemini(V3, prompt), citations)
        answer = f"### Llama\n{llama}\n\n### Gemini\n{gemini}"
    else:
        raise ValueError("Mode must be mock, llama, gemini, or compare.")
    result = {"answer": answer, "citations": citations, "department": department,
              "cache_hit": False, "similarity": similarity, "escalated": False, "mode": mode}
    cache.store(question, answer, citations, contexts, mode)
    return result
