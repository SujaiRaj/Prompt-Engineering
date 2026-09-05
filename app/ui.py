from __future__ import annotations

import streamlit as st

from .config import MODEL_MODE
from .llm import health
from .service import ask

st.set_page_config(page_title="HR Onboarding Copilot", page_icon="👥")
st.title("HR Onboarding Copilot")
st.caption("Northwind Retail Co. • Synthetic demo data only")
mode = st.selectbox("Model mode", ["mock", "llama", "gemini", "compare"], index=["mock", "llama", "gemini", "compare"].index(MODEL_MODE) if MODEL_MODE in ["mock", "llama", "gemini", "compare"] else 0)
st.info(f"Active mode: **{mode.upper()}**" + (" — development-only results, not real model evaluation." if mode == "mock" else ""))
with st.expander("Provider health"):
    st.json(health())
question = st.text_input("Ask an onboarding question", placeholder="How many annual leave days do employees receive?")
if st.button("Ask", type="primary") and question.strip():
    try:
        result = ask(question, mode)
        if result["escalated"]:
            st.error("Human escalation required")
        else:
            st.success("CACHE HIT" if result["cache_hit"] else "CACHE MISS")
        st.markdown(result["answer"])
        st.caption(f"Department: {result['department']} | Similarity: {result['similarity']:.3f}")
        if result["citations"]:
            st.write("Citations: " + " ".join(result["citations"]))
    except Exception as exc:
        st.error(str(exc))
