import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_build_with_empty_posts(tmp_path):
    posts = tmp_path / "posts"
    posts.mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "inspiration", "build", "--posts", str(posts)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    index = REPO / ".build" / "html" / "index.html"
    assert index.is_file()
    text = index.read_text(encoding="utf-8")
    assert "No posts yet" in text


def test_build_with_fixture_posts(tmp_path):
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
    media_dest = posts / "9990001112223334444" / "media"
    shutil.copytree(media_src, media_dest)

    result = subprocess.run(
        [sys.executable, "-m", "inspiration", "build", "--posts", str(tmp_path / "posts")],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    post_html = REPO / ".build" / "html" / "posts" / "9990001112223334444.html"
    assert post_html.is_file()
    html = post_html.read_text(encoding="utf-8")
    assert "blockquote" in html
    assert "careful reasoning assistant" in html
    assert "<details" not in html.lower()
    assert "updated" in html.lower()
    thumb = REPO / ".build" / "html" / "posts" / "2026" / "03" / "25" / "9990001112223334444" / "media" / "0.webp"
    assert thumb.is_file()
