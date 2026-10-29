import json
from pathlib import Path

from inspiration.index_terms import (
    build_post_index_lines,
    is_username_like,
    normalize_index_term,
    normalized_index_terms_for_post,
)
from inspiration.topics import load_topics

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "sample" / "fixtures" / "9990001112223334444.json"


def test_normalize_strips_hash_and_lowercases():
    corpus = frozenset({"mcp", "aiagent"})
    assert normalize_index_term("#MCP", corpus) == "mcp"
    assert normalize_index_term("#Mcp", corpus) == "mcp"
    assert normalize_index_term("AIAgents", corpus) == "aiagent"


def test_plural_collapse_with_corpus():
    corpus = frozenset({"aiagent", "gpu", "localllm"})
    assert normalize_index_term("aiagents", corpus) == "aiagent"
    assert normalize_index_term("gpus", corpus) == "gpu"
    assert normalize_index_term("LocalLLMs", corpus) == "localllm"


def test_usernames_rejected():
    assert is_username_like("@example_dev")
    assert normalize_index_term("@example_dev", None) is None
    assert normalize_index_term("example_dev_fixture", None) is None


def test_fixture_index_uses_single_entries_only():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    topics = {t.slug: t for t in load_topics(REPO / "topics.yaml")}
    corpus = frozenset(
        {
            "localllm",
            "reasoningmodel",
            "local-models",
            "local-model",
            "mcp",
        }
    )
    lines = build_post_index_lines(data, topics_by_slug=topics, corpus=corpus)
    joined = "\n".join(lines)
    assert "pair:" not in joined
    assert "single: local-model" in joined
    assert "single: localllm" in joined or "single: reasoningmodel" in joined
    terms = normalized_index_terms_for_post(data, topics_by_slug=topics, corpus=corpus)
    assert "example" not in " ".join(terms)
    assert all(not t.startswith("@") for t in terms)


def test_keywords_are_normalized():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["keywords"] = ["#GPU", "AIAgents"]
    topics = {t.slug: t for t in load_topics(REPO / "topics.yaml")}
    corpus = frozenset({"gpu", "aiagent"})
    terms = normalized_index_terms_for_post(data, topics_by_slug=topics, corpus=corpus)
    assert "gpu" in terms
    assert "aiagent" in terms
