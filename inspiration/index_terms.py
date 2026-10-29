"""Deterministic extraction of Sphinx index terms from post JSON."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from inspiration.topics import Topic

# Lowercase tokens to drop from auto-extracted noun singles.
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "not",
        "of",
        "on",
        "or",
        "paraphrased",
        "post",
        "summary",
        "test",
        "tests",
        "that",
        "the",
        "their",
        "they",
        "this",
        "to",
        "verbatim",
        "was",
        "with",
    }
)

_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_TEXT_RE = re.compile(r"\[([^\]]+)\]\(")
_CAMEL_RE = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-zA-Z0-9]+)+\b")
_HYPHEN_NAME_RE = re.compile(r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b")
_CAP_PHRASE_RE = re.compile(
    r"\b(?:[A-Z][a-z0-9]+(?:[A-Z][a-zA-Z0-9]+)*)(?:\s+(?:[A-Z][a-z0-9]+(?:[A-Z][a-zA-Z0-9]+)*)){1,3}\b"
)
_GITHUB_REPO_RE = re.compile(r"github\.com/([^/]+/[^/#?]+)")


def _clean_term(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.strip(".,;:!?\"'()[]")
    return text


def _is_valid_single(term: str) -> bool:
    if len(term) < 2 or len(term) > 120:
        return False
    lower = term.lower()
    if lower in _STOPWORDS:
        return False
    if "(" in term and ")" not in term:
        return False
    if term.endswith(")") and "(" not in term:
        return False
    if term.startswith("http"):
        return False
    return True


def extract_noun_singles(data: dict[str, Any]) -> list[str]:
    """Noun singles for Sphinx ``single:`` entries (keywords override auto extraction)."""
    if data.get("keywords"):
        out: list[str] = []
        seen: set[str] = set()
        for raw in data["keywords"]:
            term = _clean_term(str(raw))
            key = term.lower()
            if term and key not in seen and _is_valid_single(term):
                seen.add(key)
                out.append(term)
        return out

    candidates: list[str] = []
    author = data.get("author") or {}
    if author.get("name"):
        candidates.append(str(author["name"]))
    handle = str(author.get("handle", "")).lstrip("@")
    if handle:
        candidates.append(f"@{handle}")

    summary = str(data.get("summary_md", ""))
    candidates.extend(_BOLD_RE.findall(summary))
    candidates.extend(_CODE_RE.findall(summary))
    candidates.extend(_LINK_TEXT_RE.findall(summary))
    candidates.extend(_CAMEL_RE.findall(summary))
    candidates.extend(_HYPHEN_NAME_RE.findall(summary))
    candidates.extend(_CAP_PHRASE_RE.findall(summary))

    for ref in data.get("referenced_urls") or []:
        url = str(ref.get("url", ""))
        match = _GITHUB_REPO_RE.search(url)
        if match:
            candidates.append(match.group(1))
        title = ref.get("title")
        if title:
            candidates.append(str(title))
        path = urlparse(url).path.rstrip("/").split("/")[-1]
        if path and "." not in path and len(path) > 2:
            candidates.append(path.replace("-", " "))

    out = []
    seen: set[str] = set()
    for raw in candidates:
        term = _clean_term(raw)
        key = term.lower()
        if not term or key in seen or not _is_valid_single(term):
            continue
        seen.add(key)
        out.append(term)
    return out


def build_post_index_lines(
    data: dict[str, Any],
    *,
    topics_by_slug: dict[str, Topic],
) -> list[str]:
    """Lines for a MyST ``{index}`` directive body."""
    lines: list[str] = []

    for tag in data.get("hashtags") or []:
        tag = str(tag).lstrip("#").strip()
        if tag:
            lines.append(f"   pair: Hashtags; #{tag}")

    for slug in data.get("topics") or []:
        topic = topics_by_slug.get(str(slug))
        if topic:
            lines.append(f"   pair: Topics; {topic.title}")

    for noun in extract_noun_singles(data):
        # Escape nothing — Sphinx index entries are plain text.
        lines.append(f"   single: {noun}")

    return lines


def render_myst_index_block(lines: list[str]) -> list[str]:
    if not lines:
        return []
    return [
        "```{eval-rst}",
        ".. index::",
        *lines,
        "```",
        "",
    ]
