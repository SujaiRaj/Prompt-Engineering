# PROJECT_SPEC_MINI.md
## HR Onboarding Copilot — Mini Project Specification

**Guiding rule for every decision in this document: build the smallest system that still satisfies the assignment.** No microservices, no Kubernetes, no production architecture, no large evaluation framework. If something isn't required to demonstrate RAG + Llama/Gemini + semantic cache + escalation + a small comparison, it's cut.

---

## 0. QUICK START

```bash
# 1. Create and activate a virtual environment (Windows)
python -m venv venv
venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# fill in GEMINI_API_KEY, leave Llama defaults as-is

# 4. Start local Llama (Ollama)
ollama serve
ollama pull llama3.1:8b

# 5. Ingest the HR documents
python -m app.rag ingest

# 6. Run the app
python -m app.main
# or: streamlit run app/ui.py   (if using Streamlit for the UI)

# 7. Open the browser
# http://localhost:8000  (or the Streamlit URL printed in the terminal)
```

Build order: Phases 1–10 in Section 12. Priority order if time runs short: **RAG + citations + Llama + Gemini + semantic cache + escalation + UI working > everything else** (see Section 13).

---

## 1. PROJECT SUMMARY

**Title:** HR Onboarding Copilot
**Idea:** A RAG-based HR assistant that answers common onboarding questions from a small synthetic HR knowledge base, lets you compare a local Llama model against Gemini, demonstrates a real semantic cache, and safely escalates sensitive HR questions to a human instead of answering them.

---

## 2. WHAT GETS BUILT (and nothing more)

1. Small synthetic HR dataset (6–8 documents)
2. RAG pipeline (chunk → embed → retrieve → cite)
3. Semantic cache (real embedding similarity, not string match)
4. Sensitive-question escalation (deterministic rules)
5. Llama integration (local, via Ollama-compatible endpoint)
6. Gemini integration (API)
7. Prompt comparison (3 versions, small manual eval)
8. Basic Llama vs Gemini comparison (8–10 questions)
9. Simple UI (single page)
10. Small evaluation (15–20 questions, mostly manual scoring)

Everything else — large test suites, big benchmarks, complex architecture — is explicitly out of scope (Section 13).

---

## 3. HR DATASET (SMALL)

Fictional company: **Northwind Retail Co.** Create **6–8** synthetic Markdown documents in `data/hr_documents/`:

1. Leave Policy
2. Parental Leave Policy
3. IT Setup Guide
4. Expense Reimbursement Policy
5. Facilities / Office Guide
6. Who to Contact FAQ
7–8. (optional, only if genuinely useful — e.g. a short Attendance Policy)

Every document must open with:
```
> ⚠️ Synthetic demo document for Northwind Retail Co. — not a real company policy.
```

Each document needs simple frontmatter and numbered sections:
```yaml
---
title: "Employee Leave Policy"
department: "HR"
version: "1"
effective_date: "2026-01-01"
---
```
```markdown
## 2.1 Annual Leave
Employees receive 20 days of annual leave per year.
```

Create **one deliberate second version** of the Leave Policy (`version: "2"`, 24 days instead of 20) to demonstrate cache staleness in Section 8. That's the only versioning needed — don't version every document.

---

## 4. RAG PIPELINE (SIMPLE)

```
Question → rule-based classification → sensitive check → semantic cache lookup
  → (miss) retrieve top-k chunks → build prompt → Llama or Gemini → answer + citation
  → cache the answer (if not sensitive)
```

- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (local, no API key, fast on CPU).
- **Vector store:** Chroma (simplest local, persists to `vectorstore/`). FAISS is an acceptable substitute — pick one, don't build both.
- **Chunking:** one sensible default — **chunk size ≈ 400 tokens, overlap ≈ 60 tokens** — configurable via `.env`, but **no ablation study required**. Just use it.
- **Retrieval:** top-k = 3.

No retrieval-optimization experiments. No multiple embedding models. One embedding model, one vector store, done.

---

## 5. CITATIONS (SIMPLE)

Format: `[Source: Employee Leave Policy, Section 2.1]`. Implementation: pass document title + section into the prompt alongside each retrieved chunk, and instruct the model to cite using that exact format. A citation is "correct enough" if it names a document/section that was actually in the retrieved context — a full automated validator is not required; a light manual/spot-check is sufficient for this mini-project.

---

## 6. QUESTION CLASSIFICATION (RULE-BASED)

Simple keyword/rule classifier — **no LLM call needed for this step**:

```python
def classify(question: str) -> str:
    # keyword match against small dictionaries per category
    # returns one of: HR, IT, Finance, Facilities, General, Sensitive
```

Categories: HR, IT, Finance, Facilities, General, Sensitive. This exists for routing/display in the UI, not as a research contribution — keep it to keyword lists, don't build an ML classifier.

---

## 7. HUMAN ESCALATION (REQUIRED, KEEP SIMPLE)

Deterministic keyword rules only — **the LLM never decides this**. If any of the following appear (or are clearly implied), skip RAG generation and return an escalation message instead:

- harassment, discrimination, bullying, retaliation
- salary/pay disputes
- serious workplace complaints, legal complaints
- (sensitive-adjacent) medical conditions, disability accommodation, pregnancy-related personal circumstances

```python
def is_sensitive(question: str) -> bool:
    return any(keyword in question.lower() for keyword in SENSITIVE_KEYWORDS)
```

Escalation message example:
> "This question requires human HR assistance. Please contact the HR Conduct Team (hr-conduct@northwindretail.example)."

This is a single keyword-list function — do not build a multi-layer safety architecture on top of it.

---

## 8. SEMANTIC CACHE (REQUIRED — CORE ADVANCED COMPONENT)

Real embedding-based cache, not a string dictionary:

```
1. Embed incoming question (same embedding model as RAG).
2. Compare against embeddings of previously cached questions (cosine similarity).
3. If similarity >= SEMANTIC_CACHE_THRESHOLD (default 0.88, configurable) AND
   the cached entry's document version still matches the current version:
       → return cached answer, mark cache_hit = true, show similarity score.
4. Else:
       → run RAG pipeline normally, then store the new answer in the cache
         (skip caching if the question was escalated as sensitive).
```

Cache entry: `{question, embedding, answer, citations, document_version, timestamp}`. No large threshold-optimization study — just **demonstrate**:

- **Hit:** "What is the annual leave allowance?" vs "How many yearly leave days do employees receive?" → same cached answer, show similarity score.
- **Miss:** "How many annual leave days do employees receive?" vs "Can unused leave be carried forward?" → different question, correctly not reused, show similarity score.

---

## 9. CACHE STALENESS (SIMPLE VERSION CHECK)

Each cache entry stores which document version it was generated from. On lookup, compare that stored version against the current version of the same document in the corpus. If it doesn't match → treat as a miss, discard the stale entry. Demonstrate with the Leave Policy v1→v2 change from Section 3 (20 days → 24 days): ask the same question before and after bumping the version and re-ingesting; the cached v1 answer must not be served after the update. That's the entire staleness mechanism — no TTL, no fingerprint hashing, no invalidation queue.

---

## 10. LLAMA INTEGRATION

Local model via an OpenAI-compatible endpoint (Ollama recommended default).

```
LLAMA_BASE_URL=http://localhost:11434/v1
LLAMA_MODEL=llama3.1:8b
```

A single function `call_llama(system_prompt, user_prompt) -> str` in `app/llm.py`, called from the same RAG pipeline as Gemini.

---

## 11. GEMINI INTEGRATION

```
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
```

A single function `call_gemini(system_prompt, user_prompt) -> str` in the same `app/llm.py`. User selects **Llama / Gemini / Compare** in the UI. One lightweight `LLMProvider`-style function pair is enough — no provider class hierarchy required, though a thin abstraction (`call_model(provider, ...)`) is fine and keeps `app/rag.py` from caring which model it's calling.

---

## 12. PROMPT ENGINEERING (3 VERSIONS, SMALL COMPARISON)

`app/prompts.py`:

- **V1 — Basic:** "Answer the question using the context below."
- **V2 — RAG-grounded:** adds "only use the provided context; say if you don't know; cite the source."
- **V3 — Improved:** adds role ("You are an HR onboarding assistant for Northwind Retail Co."), explicit no-hallucination rule, required citation format, instruction to state uncertainty, and a concise-output instruction.

Run **8–10** questions through all three, record a simple table (manual scoring is fine):

| Question | Prompt | Answer Quality | Citation Quality | Hallucination? |
|---|---|---|---|---|

No large automated scoring pipeline — a spreadsheet/CSV filled in by hand is acceptable and expected.

---

## 13. LLAMA VS GEMINI COMPARISON (SMALL)

Use the **same 8–10 questions**, same retrieved context, same system prompt (V3), for both models. Record:

| Question | Llama Answer | Gemini Answer | Groundedness | Citation Quality | Latency |
|---|---|---|---|---|---|

**Academic framing (important — do not oversimplify):** don't call Llama "white-box" and Gemini "black-box." Describe it as comparing a **locally controlled, open-weight model (Llama)** against an **API-only, closed model (Gemini)** — running locally doesn't mean any interpretability/weight-inspection work was actually done here.

Manual scoring is fine. No automated benchmark harness required.

---

## 14. EVALUATION (SMALL)

`data/evaluation_questions.json` — **15–20 questions**, covering: normal HR, IT, Finance, Facilities, a paraphrase, an unknown/out-of-corpus question, a sensitive question, an adversarial question, one cache-hit case, one cache-miss case.

Metrics to record (manual scoring where automation isn't trivial):
1. Answer correctness
2. Groundedness
3. Citation correctness
4. Escalation correctness
5. Latency
6. Cache hit rate

No Recall@K/Precision@K, no statistical significance testing, no automated LLM-judge pipeline required.

---

## 15. CACHE BENEFIT DEMONSTRATION (SMALL)

Use **15–20** repeated/paraphrased questions (a subset of or similar to Section 14's set). Run once **without** cache, once **with** cache. Record: number of LLM calls, cache hits, approximate latency, approximate token/cost saving (label these **estimated**, not measured, for the Gemini cost figure specifically). This is a demonstration, not a formal benchmark — a simple before/after table is enough.

---

## 16. SIMPLE UI

One page. Streamlit is the easiest route for a mini-project (fastest to build, no separate frontend/backend split needed); a single-page HTML+JS talking to a small FastAPI/Flask backend is an acceptable alternative if preferred. Either way, the page needs only:

- Question input box
- Model selector: Llama / Gemini / Compare
- Submit button
- Answer display
- Citation(s) display
- Department/classification tag
- Cache hit/miss indicator (with similarity score if hit)
- Escalation status (shown clearly if the question was escalated instead of answered)

No admin dashboard, no auth, no multi-page navigation.

---

## 17. LoRA / QLoRA — CONCEPTUAL ONLY (≈1 PAGE OF THE REPORT)

**No training code, no training dataset required unless trivially easy to include as an illustrative example.** The report (not the code) should cover, briefly:

- Why LoRA/QLoRA *could* be used to adapt the assistant's **tone** to match a specific HR team's phrasing — and why QLoRA in particular is the more practical choice at small-org/limited-GPU scale (4-bit quantized base + small trainable adapters, far lower memory than full fine-tuning).
- Why RAG — not fine-tuning — should remain the source of **policy knowledge**, since policies change and fine-tuned facts go stale invisibly; a fine-tuned model should never be relied on to "remember" the current leave-day count.
- What real training data would need to look like (input/output pairs of employee question → HR-styled, policy-grounded answer), briefly noting anonymization/PII removal as a prerequisite before any real chat logs could be used.
- The risk that if historical HR chat logs contain one staff member's biased phrasing, a tone-adapter trained on them could learn and generalize that bias — mitigated by review/auditing of training examples before use, not by the code in this project.

Keep this to about one page in the final report — it's a required discussion, not a required implementation.

---

## 18. ETHICS (FOCUSED)

Cover only what's relevant to this project: hallucination risk, outdated-policy risk (why cache staleness handling matters), privacy (don't answer with another employee's specific case details), bias (in the corpus and, conceptually, in any future fine-tuning), the reason sensitive HR questions need human oversight, and the risk of a stale semantic cache serving an outdated answer.

**Answer directly:** where should the system stop and hand off to a human? A plain **policy lookup** ("how many leave days do I get") can usually be answered from documents. An **individual sensitive decision or complaint** (harassment, a specific medical/personal situation, a pay dispute) needs a human, because it requires judgment about that person's circumstances that a document lookup can't provide and shouldn't be trusted to guess at.

---

## 19. PROJECT STRUCTURE (SMALL)

```text
hr-onboarding-copilot/
│
├── app/
│   ├── main.py          # app entrypoint (FastAPI/Flask) — or omit if using pure Streamlit
│   ├── rag.py            # ingest, chunk, embed, retrieve
│   ├── cache.py          # semantic cache (embed, compare, store, invalidate)
│   ├── safety.py         # rule-based classification + sensitive-question check
│   ├── llm.py            # call_llama(), call_gemini()
│   ├── prompts.py        # V1, V2, V3 prompt templates
│   └── ui.py              # Streamlit page, or templates/ if HTML+JS
│
├── data/
│   ├── hr_documents/      # 6–8 markdown files
│   └── evaluation_questions.json
│
├── vectorstore/            # Chroma persistence
├── cache/                   # cached query/answer pairs
├── experiments/              # prompt comparison, model comparison, cache benefit CSVs
│
├── .env.example
├── requirements.txt
├── README.md
└── PROJECT_SPEC_MINI.md
```

No `api/` folder, no `routing/` folder, no `evaluation/` package — small enough to live as top-level scripts/notebooks if that's simpler for the student.

---

## 20. TESTING (SMALL)

Only the essentials, in one `tests/` file or a couple of files:

- Normal RAG answer returns a non-empty, cited answer
- Citation format is present in the output
- A known sensitive question is escalated, not answered
- A known paraphrase produces a cache hit
- A known distinct question produces a cache miss
- After a policy version bump, the old cached answer is not reused

No unit/integration/model test split, no CI pipeline required — a single `pytest tests/` run covering the six checks above is sufficient.

---

## 21. REQUIRED DEMO (8 SCENARIOS + 1 COMPARISON)

1. Normal HR question
2. IT question
3. Finance question
4. Unknown/missing-policy question (should say "not found," not guess)
5. Sensitive question → escalation message shown
6. Paraphrased question → cache hit (show similarity score)
7. Related-but-different question → cache miss (show similarity score)
8. Policy version update → previously cached answer is no longer reused

Then: **one** Llama vs Gemini side-by-side comparison on any question from above.

---

## 22. REPORT & SCREENSHOTS

**Report (10–15 pages), 10 sections:** Abstract · Introduction & Problem Statement · Literature Review · Proposed System & Architecture · Dataset & RAG Implementation · Prompt Engineering & Model Implementation · Semantic Cache & Safety Mechanism · Experimental Setup & Results · Ethical Evaluation, Limitations & LoRA/QLoRA · Conclusion & References.

**~8–10 screenshots:** main UI · HR corpus (folder or one doc) · RAG answer with citation · prompt V3/comparison table · sensitive-question escalation · cache HIT · cache MISS · policy update / stale-cache invalidation · Llama vs Gemini comparison · final results table/chart.

**Result tables/charts — only 4:** Prompt V1 vs V2 vs V3 · Llama vs Gemini · with-cache vs without-cache · small evaluation summary.

---

## 23. IMPLEMENTATION PRIORITY

**High priority (must work):** RAG, citations, Llama, Gemini, semantic cache, sensitive escalation, UI.
**Medium priority:** prompt experiment, small evaluation, cache benefit demo, model comparison.
**Low priority (cut first if short on time):** code polish, extensive tests, retrieval optimization, advanced UI.

If there's ever a tradeoff between a working core feature and extra analysis, **build the working core feature.**

---

## 24. EXPLICITLY OUT OF SCOPE

Do not build: 15+ documents, 35–45 evaluation questions, 60–80 cache benchmark queries, a large automated evaluation framework, an extensive unit/integration/model test suite, a complex multi-layer API architecture, microservices, a React frontend, authentication, cloud deployment, Kubernetes, a multi-agent framework, actual LoRA/QLoRA training, observability/monitoring infrastructure, multiple embedding models, multiple vector databases, large-scale benchmarking, or statistical significance testing.

---

## 25. IMPLEMENTATION PHASES

| Phase | Objective | Tasks | Expected Output | Verify |
|---|---|---|---|---|
| 1. Setup | Scaffold project | venv, requirements.txt, folder structure, `.env.example` | Folder tree matches Section 19 | `pip install -r requirements.txt` succeeds |
| 2. HR Dataset | Write corpus | 6–8 markdown docs + one versioned pair (leave policy v1/v2) | `data/hr_documents/*.md` | Docs have frontmatter + numbered sections |
| 3. RAG | Chunk, embed, retrieve | `app/rag.py`: ingest + retrieve functions | `vectorstore/` populated | A test query returns plausible chunks |
| 4. Llama + Gemini | Wire both providers | `app/llm.py` | — | Both `call_llama()` and `call_gemini()` return text |
| 5. Safety/Escalation | Rule-based classify + sensitive check | `app/safety.py` | — | Known sensitive question is correctly flagged |
| 6. Semantic Cache | Embed, compare, store, invalidate | `app/cache.py` | `cache/` | Hit/miss/staleness demo (Section 21 items 6–8) work |
| 7. Prompt Experiment | 3 prompt versions, small comparison | `app/prompts.py` + `experiments/prompt_comparison.csv` | Table filled for 8–10 questions | Manually reviewed |
| 8. Small Evaluation | Run 15–20 eval questions | `experiments/evaluation_results.csv` | All 6 metrics from Section 14 recorded | Spot-check a few rows |
| 9. UI + Final Demo | Build the single-page UI | `app/ui.py` | UI runs locally | Walk through all 8 demo scenarios (Section 21) |
| 10. Documentation | README, report data, screenshots | `README.md`, `experiments/*` finalized | Report/PPT can be assembled from these files | All Section 22 tables/screenshots obtainable |

---

## 26. DEFINITION OF DONE

- [ ] Synthetic HR documents exist (6–8, including one versioned leave-policy pair)
- [ ] RAG retrieves relevant chunks for a range of test questions
- [ ] Answers include citations in the correct format
- [ ] Llama integration works
- [ ] Gemini integration works
- [ ] Sensitive questions are escalated, not answered
- [ ] Semantic cache works (embedding similarity, not string match)
- [ ] Cache hit demonstrated with similarity score shown
- [ ] Cache miss demonstrated with similarity score shown
- [ ] Stale-cache protection demonstrated via a real policy version bump
- [ ] Prompt V1/V2/V3 compared on 8–10 questions
- [ ] Llama vs Gemini compared on 8–10 questions, with accurate white-box/black-box framing
- [ ] Small evaluation (15–20 questions) completed with the 6 metrics recorded
- [ ] Cache benefit demonstrated (with vs without cache, 15–20 questions)
- [ ] UI works end-to-end for all 8 demo scenarios
- [ ] Screenshots can be captured for all items in Section 22
- [ ] Report and PPT can be assembled from `experiments/` outputs without additional work

**The project is done when every box above is checked — nothing more is required, and nothing on the Section 24 exclusion list should have been built.**
