from __future__ import annotations

V1 = "Answer the question using the context below."
V2 = "Use only the provided context. If it does not answer the question, say so. Cite the source."
V3 = """You are an HR onboarding assistant for Northwind Retail Co. Answer only from the provided context.
Do not invent facts. If the context does not contain the answer, say that the policy information was not found.
Keep the answer concise and include citations exactly as [Source: Document Name, Section X.X]."""

PROMPTS = {"V1": V1, "V2": V2, "V3": V3}

def build_user_prompt(question: str, contexts: list[dict]) -> str:
    blocks = []
    for item in contexts:
        meta = item["metadata"]
        blocks.append(f"[Source: {meta['title']}, Section {meta['section']}]\n{item['text']}")
    return f"Context:\n{'\n\n'.join(blocks)}\n\nQuestion: {question}"
