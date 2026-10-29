"""Build per-term index pages and the site-wide A–Z term listing."""

from __future__ import annotations

import html
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from inspiration.index_terms import (
    build_index_corpus,
    normalized_index_terms_for_post,
)
from inspiration.posts import PostRecord
from inspiration.topics import Topic

_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class TermPage:
    term: str
    slug: str
    posts: tuple[PostRecord, ...]


def slug_for_term(term: str, slug_owner: dict[str, str]) -> str:
    """URL-safe slug; disambiguate on collision with a numeric suffix."""
    base = _SLUG_RE.sub("-", term.lower()).strip("-") or "term"
    slug = base
    suffix = 2
    while slug in slug_owner and slug_owner[slug] != term:
        slug = f"{base}-{suffix}"
        suffix += 1
    slug_owner[slug] = term
    return slug


def build_term_pages(
    records: list[PostRecord],
    *,
    topics_by_slug: dict[str, Topic],
    corpus: frozenset[str],
) -> tuple[list[TermPage], dict[str, str]]:
    """Map normalized terms to posts (newest first) and term→slug lookup."""
    by_term: dict[str, list[PostRecord]] = defaultdict(list)
    for rec in records:
        for term in normalized_index_terms_for_post(
            rec.data, topics_by_slug=topics_by_slug, corpus=corpus
        ):
            by_term[term].append(rec)

    slug_owner: dict[str, str] = {}
    term_to_slug: dict[str, str] = {}
    pages: list[TermPage] = []

    for term in sorted(by_term.keys(), key=str.lower):
        posts = by_term[term]
        posts.sort(key=lambda r: (r.updated_at, r.id), reverse=True)
        slug = slug_for_term(term, slug_owner)
        term_to_slug[term] = slug
        pages.append(TermPage(term=term, slug=slug, posts=tuple(posts)))

    return pages, term_to_slug


def _strip_md(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`#>]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def summary_snippet(record: PostRecord, *, max_len: int = 220) -> str:
    data = record.data
    base = str(data.get("relevance") or "")
    if not base:
        base = _strip_md(str(data.get("summary_md", "")))
    if len(base) <= max_len:
        return base
    return base[: max_len - 1].rstrip() + "…"


def _author_line(data: dict[str, Any]) -> str:
    author = data["author"]
    handle = author["handle"]
    if not handle.startswith("@"):
        handle = f"@{handle}"
    return f"{author['name']} ({handle})"


def _post_heading(record: PostRecord, topic_map: dict[str, Topic]) -> str:
    topics = ", ".join(
        topic_map[s].title if s in topic_map else s for s in record.data.get("topics", [])
    )
    return f"{_author_line(record.data)} — {topics or 'uncategorized'}"


def render_term_page_md(page: TermPage, *, topic_map: dict[str, Topic]) -> str:
    count = len(page.posts)
    plural = "posts" if count != 1 else "post"
    lines = [
        f"# {page.term}",
        "",
        f"{count} {plural} indexed under this term (newest first).",
        "",
        "## Posts",
        "",
    ]
    for rec in page.posts:
        data = rec.data
        heading = html.escape(_post_heading(rec, topic_map))
        snippet = html.escape(summary_snippet(rec))
        updated = html.escape(str(data["updated_at"]))
        lines.extend(
            [
                f"### {heading}",
                "",
                f"**Updated:** {updated}",
                "",
                f"<p>{snippet}</p>",
                "",
                f'* <a href="../posts/{rec.id}.html">Read full post</a>',
                "",
            ]
        )
    lines.extend(
        [
            "## Browse",
            "",
            '* <a href="../terms-index.html">A–Z index of all terms</a>',
            "",
        ]
    )
    return "\n".join(lines)


def render_terms_index_rst(pages: list[TermPage]) -> str:
    """RST wrapper with raw HTML A–Z listing."""
    by_letter: dict[str, list[TermPage]] = defaultdict(list)
    for page in pages:
        first = page.term[0].lower() if page.term else ""
        letter = first if first.isalpha() else "#"
        by_letter[letter].append(page)

    letters = sorted((k for k in by_letter.keys() if k != "#"), key=str.lower)
    if "#" in by_letter:
        letters.append("#")

    jump_parts = [
        f'<a class="index-jump" href="#index-letter-{html.escape(ch, quote=True)}">{html.escape(ch.upper() if ch != "#" else "#")}</a>'
        for ch in letters
    ]
    jump_html = " · ".join(jump_parts)

    sections: list[str] = []
    for ch in letters:
        label = ch.upper() if ch != "#" else "0–9 / symbols"
        sections.append(
            f'<h2 id="index-letter-{html.escape(ch, quote=True)}">{html.escape(label)}</h2>'
        )
        sections.append('<ul class="term-index-list">')
        for page in sorted(by_letter[ch], key=lambda p: p.term.lower()):
            count = len(page.posts)
            term = html.escape(page.term)
            slug = html.escape(page.slug, quote=True)
            sections.append(
                f'<li><a href="terms/{slug}.html">{term}</a> ({count})</li>'
            )
        sections.append("</ul>")

    body = "\n   ".join(sections)
    return "\n".join(
        [
            "Index",
            "=====",
            "",
            "Alphabetical list of normalized hashtags, topics, keywords, and extracted nouns.",
            "",
            ".. raw:: html",
            "",
            f'   <nav class="index-jumps">{jump_html}</nav>',
            "",
            f"   {body}",
            "",
        ]
    )


def build_site_terms(
    records: list[PostRecord],
    *,
    topics: list[Topic],
) -> tuple[list[TermPage], dict[str, str], frozenset[str]]:
    topic_map = {t.slug: t for t in topics}
    corpus = build_index_corpus(records, topics_by_slug=topic_map)
    pages, term_to_slug = build_term_pages(
        records, topics_by_slug=topic_map, corpus=corpus
    )
    return pages, term_to_slug, corpus
