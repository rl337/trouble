"""Generate Sphinx source files from validated posts."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from inspiration.posts import PostRecord
from inspiration.topics import Topic


def _format_day_heading(day_key: str) -> str:
    dt = datetime.strptime(day_key, "%Y-%m-%d")
    return dt.strftime("%A, %B %d, %Y").replace(" 0", " ")


def _author_line(data: dict[str, Any]) -> str:
    author = data["author"]
    handle = author["handle"]
    if not handle.startswith("@"):
        handle = f"@{handle}"
    return f"{author['name']} ({handle})"


def _post_title(record: PostRecord) -> str:
    topics = ", ".join(record.data.get("topics", []))
    return f"{_author_line(record.data)} — {topics}"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _thumb_href_from_repo_path(thumbnail: str) -> str:
    if not thumbnail.startswith("posts/"):
        return thumbnail
    return thumbnail[len("posts/") :]


def _blockquote(text: str) -> list[str]:
    lines = ["", "> " + text.replace("\n", "\n> "), ""]
    return lines


def _render_media_items(media: list[dict[str, Any]]) -> list[str]:
    if not media:
        return []

    out = ["## Media", ""]
    for item in media:
        media_type = item["type"]
        kind = item.get("kind")
        kind_suffix = f" ({kind})" if kind else ""
        out.append(f"**{media_type}**{kind_suffix}: {item['description']}")
        out.append("")

        url = item["url"]
        thumb = item.get("thumbnail")
        ocr = item.get("ocr_text")

        if media_type == "image" and thumb:
            href = _thumb_href_from_repo_path(thumb)
            out.append(f"[![{item['description']}]({href})]({url})")
            out.append("")
        elif media_type in ("image", "gif"):
            out.append(f"[View original {media_type}]({url})")
            out.append("")
        elif media_type == "video":
            out.append(f"[View video]({url})")
            out.append("")

        if ocr:
            out.extend(_blockquote(ocr))

    return out


def _index_entry_line(rec: PostRecord) -> str:
    marker = " *(updated)*" if rec.was_updated else ""
    return f"* :doc:`posts/{rec.id}` — {rec.data['relevance']}{marker}"


def generate_sphinx_sources(
    *,
    records: list[PostRecord],
    topics: list[Topic],
    out_dir: Path,
) -> None:
    """Write generated .rst and .md files under out_dir."""
    if out_dir.exists():
        import shutil

        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    topics_dir = out_dir / "topics"
    archive_dir = out_dir / "archive"
    posts_dir = out_dir / "posts"

    by_update_day: dict[str, list[PostRecord]] = defaultdict(list)
    for rec in records:
        by_update_day[rec.update_day_key].append(rec)
    for day_records in by_update_day.values():
        day_records.sort(key=lambda r: (r.updated_at, r.id), reverse=True)

    by_archive_day: dict[str, list[PostRecord]] = defaultdict(list)
    for rec in records:
        by_archive_day[rec.day_key].append(rec)

    lines = [
        "Recent inspiration",
        "==================",
        "",
        ".. raw:: html",
        "",
        '   <p class="tagline">Curated X threads — sorted by last update (UTC), grouped by update day.</p>',
        "",
        "* :doc:`browse` — browse all topics and archive days (with post counts)",
        "",
    ]

    if not records:
        lines.extend(
            [
                "No posts yet.",
                "",
                "Agents can add JSON under ``posts/YYYY/MM/DD/`` (see ``posts/README.md`` in the repo).",
                "",
            ]
        )
    else:
        for day_key in sorted(by_update_day.keys(), reverse=True):
            heading = _format_day_heading(day_key)
            lines.append(heading)
            lines.append("-" * len(heading))
            lines.append("")
            for rec in by_update_day[day_key]:
                lines.append(_index_entry_line(rec))
            lines.append("")

    lines.extend(["Topics", "------", ""])
    for topic in topics:
        lines.append(f"* :doc:`topics/{topic.slug}` — {topic.title}")
    lines.append("")

    lines.extend(["Archives", "--------", ""])
    for day_key in sorted(by_archive_day.keys(), reverse=True):
        lines.append(f"* :doc:`archive/{day_key}` — {day_key}")
    lines.append("")

    topic_map = {t.slug: t for t in topics}
    for topic in topics:
        matching = [r for r in records if topic.slug in r.data.get("topics", [])]
        matching.sort(key=lambda r: (r.updated_at, r.id), reverse=True)
        tlines = [
            topic.title,
            "=" * len(topic.title),
            "",
            topic.description,
            "",
            "Posts",
            "-----",
            "",
        ]
        if not matching:
            tlines.append("_No posts in this topic yet._")
            tlines.append("")
        else:
            for rec in matching:
                tlines.append(f"* :doc:`../posts/{rec.id}` — {rec.data['relevance']}")
                tlines.append("")
        _write(topics_dir / f"{topic.slug}.rst", "\n".join(tlines))

    for day_key, day_records in by_archive_day.items():
        alines = [
            f"Archive: {day_key}",
            "=" * (10 + len(day_key)),
            "",
        ]
        for rec in sorted(day_records, key=lambda r: r.posted_at, reverse=True):
            alines.append(f"* :doc:`../posts/{rec.id}` — {_author_line(rec.data)}")
        alines.append("")
        _write(archive_dir / f"{day_key}.rst", "\n".join(alines))

    for rec in records:
        data = rec.data
        meta = (
            f"**Original post:** [{data['permalink']}]({data['permalink']})  \n"
            f"**Posted:** {data['posted_at']} · **Collected:** {data['collected_at']}"
        )
        if rec.was_updated:
            meta += f" · **Updated:** {data['updated_at']}"

        md_lines = [
            f"# {_post_title(rec)}",
            "",
            meta,
            "",
            "## Why it matters",
            "",
            data["relevance"],
            "",
            "## Summary",
            "",
            data["summary_md"],
            "",
        ]

        thread = data.get("thread") or []
        if thread:
            md_lines.extend(["## Thread follow-ups", ""])
            for item in thread:
                md_lines.append(
                    f"{item['position']}. [{item['permalink']}]({item['permalink']}) "
                    f"({item['posted_at']})"
                )
            md_lines.append("")

        md_lines.extend(_render_media_items(data.get("media") or []))

        refs = data.get("referenced_urls") or []
        if refs:
            md_lines.extend(["## Referenced links", ""])
            for ref in refs:
                label = ref.get("title") or ref["url"]
                md_lines.append(f"* [{label}]({ref['url']}) (from post `{ref['from_post']}`)")
            md_lines.append("")

        tags = data.get("hashtags") or []
        if tags:
            md_lines.extend(["## Hashtags", "", ", ".join(f"#{t}" for t in tags), ""])

        topic_slugs = data.get("topics", [])
        if topic_slugs:
            md_lines.extend(["## Topics", ""])
            for slug in topic_slugs:
                if slug in topic_map:
                    title = topic_map[slug].title
                    md_lines.append(f'* <a href="../topics/{slug}.html">{title}</a>')
            md_lines.append("")

        day_heading = _format_day_heading(rec.day_key)
        md_lines.extend(
            [
                "## Archive",
                "",
                f'* <a href="../archive/{rec.day_key}.html">{day_heading}</a>',
                "",
                "## Browse",
                "",
                '* <a href="../browse.html">All topics and archive days</a>',
                "",
            ]
        )

        _write(posts_dir / f"{rec.id}.md", "\n".join(md_lines))

    browse_lines = [
        "Browse",
        "======",
        "",
        "Site map of topic categories and archive days.",
        "",
        "Topics",
        "------",
        "",
    ]
    for topic in topics:
        count = sum(1 for r in records if topic.slug in r.data.get("topics", []))
        plural = "posts" if count != 1 else "post"
        browse_lines.append(
            f"* :doc:`topics/{topic.slug}` — {topic.title} ({count} {plural})"
        )
    browse_lines.extend(
        [
            "",
            "Archives by day",
            "---------------",
            "",
        ]
    )
    for day_key in sorted(by_archive_day.keys(), reverse=True):
        count = len(by_archive_day[day_key])
        plural = "posts" if count != 1 else "post"
        heading = _format_day_heading(day_key)
        browse_lines.append(
            f"* :doc:`archive/{day_key}` — {heading} ({count} {plural})"
        )
    browse_lines.append("")
    _write(out_dir / "browse.rst", "\n".join(browse_lines))

    lines.extend(
        [
            ".. toctree::",
            "   :hidden:",
            "   :maxdepth: 1",
            "",
            "   browse",
        ]
    )
    for topic in topics:
        lines.append(f"   topics/{topic.slug}")
    for day_key in sorted(by_archive_day.keys(), reverse=True):
        lines.append(f"   archive/{day_key}")
    for rec in sorted(records, key=lambda r: r.id):
        lines.append(f"   posts/{rec.id}")
    lines.append("")

    _write(out_dir / "index.rst", "\n".join(lines))
