"""Tests for Sphinx genindex population and navigation."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HTML = REPO / ".build" / "html"
FIXTURE_ID = "9990001112223334444"


def _build_fixture_site(tmp_path: Path) -> None:
    posts = tmp_path / "posts" / "2026" / "03" / "25"
    posts.mkdir(parents=True)
    fixture = REPO / "sample" / "fixtures" / f"{FIXTURE_ID}.json"
    shutil.copy(fixture, posts / fixture.name)
    media_src = (
        REPO
        / "sample"
        / "fixtures"
        / "media-assets"
        / "posts"
        / "2026"
        / "03"
        / "25"
        / FIXTURE_ID
        / "media"
    )
    shutil.copytree(media_src, posts / FIXTURE_ID / "media")
    result = subprocess.run(
        [sys.executable, "-m", "inspiration", "build", "--posts", str(tmp_path / "posts")],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout


def test_genindex_has_hashtag_topic_and_noun_entries(tmp_path):
    _build_fixture_site(tmp_path)
    genindex = HTML / "genindex.html"
    assert genindex.is_file()
    text = genindex.read_text(encoding="utf-8")
    assert len(text.strip()) > 500
    assert "LocalLLM" in text or "#LocalLLM" in text or "Hashtags" in text
    assert "Local reasoning models" in text
    assert "Example Dev" in text or "Qwen3" in text
    assert f"posts/{FIXTURE_ID}.html" in text


def test_genindex_linked_from_nav(tmp_path):
    _build_fixture_site(tmp_path)
    index = HTML / "index.html"
    text = index.read_text(encoding="utf-8")
    assert "genindex.html" in text
    assert "browse.html" in text


def test_browse_page_still_present(tmp_path):
    _build_fixture_site(tmp_path)
    browse = HTML / "browse.html"
    assert browse.is_file()
    assert "topics/local-models.html" in browse.read_text(encoding="utf-8")


def test_count_genindex_term_links(tmp_path):
    _build_fixture_site(tmp_path)
    text = (HTML / "genindex.html").read_text(encoding="utf-8")
    assert "genindex-jumpbox" in text
    entry_links = re.findall(r'class="indextable genindextable"', text)
    assert len(entry_links) >= 1
    assert text.count("posts/9990001112223334444.html") >= 3
