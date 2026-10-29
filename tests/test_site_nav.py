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


def test_genindex_has_direct_tag_links(tmp_path):
    _build_fixture_site(tmp_path)
    genindex = HTML / "genindex.html"
    text = genindex.read_text(encoding="utf-8")
    assert len(text.strip()) > 500
    assert "pair: Hashtags" not in text
    assert ">Hashtags</a>" not in text.replace(" ", "")
    # Normalized hashtag is a top-level index link target.
    assert re.search(
        r'<li><a href="posts/9990001112223334444\.html#index-0">localllm</a>',
        text,
        re.I,
    )
    assert "local-model" in text
    assert "example_dev_fixture" not in text.lower()
    assert "@example" not in text


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
