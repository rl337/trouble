import json
from pathlib import Path

from inspiration.index_terms import normalize_index_term
from inspiration.keywords_backfill import (
    curate_post_keywords,
    is_acceptable_curated_keyword,
)
from inspiration.topics import load_topics

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "sample" / "fixtures" / "9990001112223334444.json"


def test_is_acceptable_rejects_noise():
    assert is_acceptable_curated_keyword("mcp")
    assert not is_acceptable_curated_keyword("1-flash")
    assert not is_acceptable_curated_keyword("owner/repo/path")


def test_curate_fixture_keywords():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    topics = {t.slug: t for t in load_topics(REPO / "topics.yaml")}
    corpus = frozenset(
        {
            "localllm",
            "reasoningmodel",
            "local-model",
            "local-reasoning-bench",
            "model-card-fixture",
        }
    )
    keywords = curate_post_keywords(data, corpus=corpus, topics_by_slug=topics)
    assert "local-model" not in keywords
    assert "localllm" not in keywords
    assert "example" not in keywords
    assert "exampledevfixture" not in keywords
    assert all(normalize_index_term(k, corpus) == k for k in keywords)
    assert keywords
