"""Copy post media assets into the built HTML tree."""

from __future__ import annotations

import shutil
from pathlib import Path

from inspiration.posts import discover_post_files


def copy_post_media_to_site(posts_root: Path, html_out: Path) -> None:
    """Copy posts/YYYY/MM/DD/<id>/media/* into html_out/posts/YYYY/MM/DD/<id>/media/."""
    for json_path in discover_post_files(posts_root):
        media_src = json_path.parent / json_path.stem / "media"
        if not media_src.is_dir():
            continue
        rel = json_path.relative_to(posts_root).parent / json_path.stem / "media"
        dest = html_out / "posts" / rel
        dest.mkdir(parents=True, exist_ok=True)
        for item in media_src.iterdir():
            if item.is_file():
                shutil.copy2(item, dest / item.name)


def copy_fixture_media_assets(repo_root: Path, html_out: Path) -> None:
    """Copy fixture media-assets/posts/... into html_out/posts/... for local fixture builds."""
    assets_root = repo_root / "sample" / "fixtures" / "media-assets" / "posts"
    if not assets_root.is_dir():
        return
    for src in assets_root.rglob("*"):
        if src.is_file():
            rel = src.relative_to(assets_root)
            dest = html_out / "posts" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
