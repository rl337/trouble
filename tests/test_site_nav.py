"""Navigation and browse page checks on built HTML."""

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HTML = REPO / ".build" / "html"


def _build_fixture_site(tmp_path: Path) -> None:
    posts = tmp_path / "posts" / "2026" / "03" / "25"
    posts.mkdir(parents=True)
    fixture = REPO / "sample" / "fixtures" / "9990001112223334444.json"
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
        / "9990001112223334444"
        / "media"
    )
    shutil.copytree(media_src, posts / "9990001112223334444" / "media")
    result = subprocess.run(
        [sys.executable, "-m", "inspiration", "build", "--posts", str(tmp_path / "posts")],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout


def test_no_generated_genindex(tmp_path):
    _build_fixture_site(tmp_path)
    genindex = HTML / "genindex.html"
    assert not genindex.exists(), "genindex.html should not be built when html_use_index is False"


def test_browse_page_has_topic_and_archive_links(tmp_path):
    _build_fixture_site(tmp_path)
    browse = HTML / "browse.html"
    assert browse.is_file()
    text = browse.read_text(encoding="utf-8")
    assert "topics/local-models.html" in text
    assert "archive/" in text
    assert "post" in text.lower()
    assert len(text.strip()) > 200


def test_nav_links_resolve(tmp_path):
    _build_fixture_site(tmp_path)
    index = HTML / "index.html"
    browse = HTML / "browse.html"
    search = HTML / "search.html"
    post = HTML / "posts" / "9990001112223334444.html"
    topic = HTML / "topics" / "local-models.html"

    index_text = index.read_text(encoding="utf-8")
    assert "genindex.html" not in index_text
    assert "browse.html" in index_text

    for path in (index, browse, search, post, topic):
        assert path.is_file(), f"missing {path}"

    post_text = post.read_text(encoding="utf-8")
    assert "topics/local-models.html" in post_text
    assert "archive/" in post_text
    assert "browse.html" in post_text

    browse_text = browse.read_text(encoding="utf-8")
    assert 'href="browse.html"' in browse_text or "Browse" in browse_text
