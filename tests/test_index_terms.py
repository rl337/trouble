import json
from pathlib import Path

from inspiration.index_terms import build_post_index_lines, extract_noun_singles
from inspiration.topics import load_topics

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "sample" / "fixtures" / "9990001112223334444.json"


def test_fixture_index_lines_include_hashtag_topic_and_noun():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    topics = {t.slug: t for t in load_topics(REPO / "topics.yaml")}
    lines = build_post_index_lines(data, topics_by_slug=topics)
    joined = "\n".join(lines)
    assert "pair: Hashtags;" in joined
    assert "LocalLLM" in joined
    assert "pair: Topics; Local reasoning models" in joined
    nouns = extract_noun_singles(data)
    assert any("Example Dev" in n or "Qwen3" in n for n in nouns)


def test_keywords_override_auto_nouns():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["keywords"] = ["CuratedKeywordOne"]
    nouns = extract_noun_singles(data)
    assert nouns == ["CuratedKeywordOne"]
