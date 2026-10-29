"""Tests for custom term index pages."""

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


def test_term_page_lists_fixture_post(tmp_path):
    _build_fixture_site(tmp_path)
    term_page = HTML / "terms" / "localllm.html"
    assert term_page.is_file(), "expected term page for localllm"
    text = term_page.read_text(encoding="utf-8")
    assert FIXTURE_ID in text
    assert "Read full post" in text


def test_terms_index_links_to_term_page(tmp_path):
    _build_fixture_site(tmp_path)
    index = HTML / "terms-index.html"
    assert index.is_file()
    text = index.read_text(encoding="utf-8")
    assert 'href="terms/localllm.html"' in text
    assert "localllm" in text
    assert re.search(r"localllm</a>\s*\(\d+\)", text)
    assert "genindex.html" not in text
    assert not re.search(r">\[\d+\]<", text)


def test_nav_index_points_at_terms_index(tmp_path):
    _build_fixture_site(tmp_path)
    recent = HTML / "index.html"
    text = recent.read_text(encoding="utf-8")
    assert "terms-index.html" in text
    assert "genindex.html" not in text


def test_post_page_links_hashtag_to_term_page(tmp_path):
    _build_fixture_site(tmp_path)
    post = HTML / "posts" / f"{FIXTURE_ID}.html"
    text = post.read_text(encoding="utf-8")
    assert 'href="../terms/localllm.html"' in text


def test_browse_page_still_present(tmp_path):
    _build_fixture_site(tmp_path)
    browse = HTML / "browse.html"
    assert browse.is_file()
    assert "topics/local-models.html" in browse.read_text(encoding="utf-8")
