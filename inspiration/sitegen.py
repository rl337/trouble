"""Generate Sphinx source files from validated posts."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from inspiration.posts import PostRecord
from inspiration.topics import Topic


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "post"


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

    # --- index (recent, grouped by archive day from path) ---
    by_day: dict[str, list[PostRecord]] = defaultdict(list)
    for rec in records:
        by_day[rec.day_key].append(rec)

    lines = [
        "Recent inspiration",
        "==================",
        "",
        ".. raw:: html",
        "",
        '   <p class="tagline">Curated X threads — newest first, grouped by archive day.</p>',
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
        for day_key in sorted(by_day.keys(), reverse=True):
            heading = _format_day_heading(day_key)
            lines.append(heading)
            lines.append("-" * len(heading))
            lines.append("")
            for rec in by_day[day_key]:
                lines.append(f"* :doc:`posts/{rec.id}` — {rec.data['relevance']}")
            lines.append("")

    lines.extend(
        [
            "Topics",
            "------",
            "",
        ]
    )
    for topic in topics:
        lines.append(f"* :doc:`topics/{topic.slug}` — {topic.title}")
    lines.append("")

    lines.extend(
        [
            "Archives",
            "--------",
            "",
        ]
    )
    for day_key in sorted(by_day.keys(), reverse=True):
        lines.append(f"* :doc:`archive/{day_key}` — {day_key}")
    lines.append("")

    _write(out_dir / "index.rst", "\n".join(lines))

    # --- topic pages ---
    topic_map = {t.slug: t for t in topics}
    for topic in topics:
        matching = [r for r in records if topic.slug in r.data.get("topics", [])]
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

    # --- archive pages ---
    for day_key, day_records in by_day.items():
        alines = [
            f"Archive: {day_key}",
            "=" * (10 + len(day_key)),
            "",
        ]
        for rec in sorted(day_records, key=lambda r: r.posted_at, reverse=True):
            alines.append(f"* :doc:`../posts/{rec.id}` — {_author_line(rec.data)}")
        alines.append("")
        _write(archive_dir / f"{day_key}.rst", "\n".join(alines))

    # --- individual posts (MyST markdown) ---
    for rec in records:
        data = rec.data
        md_lines = [
            f"# {_post_title(rec)}",
            "",
            f"**Original post:** [{data['permalink']}]({data['permalink']})  ",
            f"**Posted:** {data['posted_at']} · **Collected:** {data['collected_at']}",
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

        refs = data.get("referenced_urls") or []
        if refs:
            md_lines.extend(["## Referenced links", ""])
            for ref in refs:
                label = ref.get("title") or ref["url"]
                md_lines.append(f"* [{label}]({ref['url']}) (from post `{ref['from_post']}`)")
            md_lines.append("")

        tags = data.get("hashtags") or []
        if tags:
            md_lines.append("## Hashtags")
            md_lines.append("")
            md_lines.append(", ".join(f"#{t}" for t in tags))
            md_lines.append("")

        topic_links = [topic_map[s].title for s in data.get("topics", []) if s in topic_map]
        if topic_links:
            md_lines.append("## Topics")
            md_lines.append("")
            md_lines.append(", ".join(topic_links))
            md_lines.append("")

        _write(posts_dir / f"{rec.id}.md", "\n".join(md_lines))
