import json
from app import cache
from app.config import CACHE_DIR
from app.embeddings import embed
from app.rag import ingest, retrieve
from app.safety import is_sensitive
from app.service import ask

def setup_function():
    cache.clear()
    ingest()

def test_rag_retrieves_leave_policy():
    chunks = retrieve("How many annual leave days do employees receive?")
    assert chunks[0]["metadata"]["title"] == "Employee Leave Policy"

def test_sensitive_question_escalates_without_model():
    result = ask("I need to report harassment by my manager", "mock")
    assert is_sensitive("harassment") and result["escalated"]
    assert "HR Conduct Team" in result["answer"]

def test_sensitive_inflection_escalates_without_model():
    assert ask("My manager is harassing me. What should I do?", "mock")["escalated"] is True

def test_semantic_cache_hit_for_same_question():
    ask("What is the annual leave allowance?", "mock")
    result = ask("How many yearly leave days do employees receive?", "mock")
    assert result["cache_hit"] is True

def test_semantic_cache_miss_for_different_question():
    ask("How many annual leave days do employees receive?", "mock")
    result = ask("Can unused leave be carried forward?", "mock")
    assert result["cache_hit"] is False

def test_mock_mode_has_citation_and_needs_no_provider():
    result = ask("Where do I collect my laptop?", "mock")
    assert result["answer"].startswith("MOCK MODE:")
    assert "[Source:" in result["answer"]

def test_version_change_invalidates_cached_answer():
    question = "How many annual leave days do employees receive?"
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / "semantic_cache.json").write_text(json.dumps([{
        "question": question, "embedding": embed([question])[0], "answer": "20 days",
        "citations": ["[Source: Employee Leave Policy, Section 2.1]"],
        "document_versions": {"Employee Leave Policy": "1"}, "mode": "mock", "timestamp": "demo"
    }]))
    entry, _ = cache.lookup(question)
    assert entry is None
