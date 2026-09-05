# HR Onboarding Copilot

A deliberately small academic mini-project: RAG over synthetic Northwind Retail Co. HR documents, deterministic safety escalation, embedding-based semantic cache, and switchable Mock, local Llama, Gemini, or comparison modes.

## Installation

### Windows (project-local environment)

Open Command Prompt and run the following from the project directory. All packages are installed into `D:\Prompt Engineering\venv`, never the global Python environment.

```bat
cd /d "D:\Prompt Engineering"
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Then use the activated environment for every project command below.

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
python -m app.rag ingest
streamlit run app/ui.py
```

The first optional `sentence-transformers` model download is intentionally not required for mock development. `USE_SENTENCE_TRANSFORMERS=false` keeps the app on its deterministic hashing embedding fallback, so retrieval and the *real embedding-similarity cache flow* work offline. On a connected real-experiment machine, pre-download `sentence-transformers/all-MiniLM-L6-v2` and set `USE_SENTENCE_TRANSFORMERS=true` to use the configured embedding model.

## Modes and configuration

`.env` defaults to `MODEL_MODE=mock`; it is ignored by Git. Mock is clearly labelled and is for UI, retrieval, cache, safety, and test development only—it must not be cited as Llama or Gemini evaluation.

- `mock`: no network, Llama runtime, or API key needed.
- `llama`: run `ollama serve`, `ollama pull llama3.1:8b`, then select Llama. The default endpoint is `http://localhost:11434/v1`.
- `gemini`: add `GEMINI_API_KEY` and optionally change `GEMINI_MODEL` in `.env`.
- `compare`: invokes both real providers for the same retrieved context. A missing provider produces an explicit error; it never silently uses Mock.

The UI displays provider health and the active mode. Sensitive questions never call any provider.

## RAG and citations

Documents live in `data/hr_documents/`. The version-1 and version-2 leave-policy files are retained for the staleness demonstration; ingestion only activates the highest version (currently v2: 24 days). Run:

```bash
python scripts/retrieval_demo.py
```

Answers cite retrieved metadata in the format `[Source: Document Name, Section X.X]`.

## Tests and demos

```bash
pytest -q
python scripts/cache_demo.py
python scripts/policy_staleness_demo.py
python scripts/prompt_comparison.py mock
```

The cache stores query embeddings, answers, citations, and document versions in `cache/semantic_cache.json`. It compares cosine similarity and discards entries whose cited document version is no longer current.

For development-only results:

```bash
python scripts/run_experiment.py mock
```

For final real experiments on the friend’s configured machine:

```bash
python scripts/run_experiment.py llama
python scripts/run_experiment.py gemini
python scripts/run_experiment.py compare
# equivalent dedicated comparison runner
python scripts/model_comparison.py
```

Results go to `experiments/` and include the mode label, citations, escalation status, and measured local elapsed time. Complete manual groundedness/citation columns only with real results for the final Llama-vs-Gemini discussion. Describe the comparison as a locally controlled open-weight Llama model versus API-only closed Gemini; no mock result, fabricated latency, or fabricated quality claim belongs in the report.

## Troubleshooting

If Streamlit says a real provider is unavailable, verify the corresponding `.env` values and runtime/API access. In mock mode this is expected and not a project failure. Re-run `python -m app.rag ingest` after editing the corpus.
