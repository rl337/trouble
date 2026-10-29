"""Curate and backfill normalized ``keywords`` on post JSON files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from inspiration.index_terms import (
    _BOLD_RE,
    _CAMEL_RE,
    _CODE_RE,
    _GITHUB_REPO_RE,
    _HYPHEN_NAME_RE,
    _LINK_TEXT_RE,
    _author_blocklist,
    _clean_raw,
    _is_blocked_candidate,
    build_index_corpus,
    clean_reference_label,
    is_username_like,
    normalize_index_term,
    normalize_topic_term,
)
from inspiration.posts import PostRecord, discover_post_files, make_validator, validate_post_file
from inspiration.topics import Topic, load_topics

_MAX_KEYWORDS = 18
_MAX_KEYWORD_LEN = 36
_SHORT_OK = frozenset({"ai", "ml", "llm", "mcp", "rag", "api", "gpu", "tpu", "vllm", "mlx", "rl", "ui"})


def is_acceptable_curated_keyword(norm: str) -> bool:
    if not norm or len(norm) > _MAX_KEYWORD_LEN:
        return False
    if len(norm) < 3 and norm not in _SHORT_OK:
        return False
    if "|" in norm or "http" in norm or norm.endswith(".git"):
        return False
    if " " in norm:
        return False
    if is_username_like(norm):
        return False
    if norm.count("/") >= 1:
        return False
    if norm.replace("-", "").replace(".", "").isdigit():
        return False
    if norm[0].isdigit() and norm[1:2] in ("-", "/", "."):
        return False
    return True


def _phrase_slug(raw: str) -> str:
    text = _clean_raw(raw).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def collect_curated_raw_candidates(data: dict[str, Any]) -> list[str]:
    """Raw noun-like strings from summary, URLs, and hashtags (pre-normalization)."""
    blocked = _author_blocklist(data)
    candidates: list[str] = []

    for tag in data.get("hashtags") or []:
        raw = str(tag).lstrip("#")
        if raw and not _is_blocked_candidate(raw, blocked):
            candidates.append(raw)

    summary = str(data.get("summary_md", ""))
    for ref in data.get("referenced_urls") or []:
        title = ref.get("title")
        url = str(ref.get("url", ""))
        if title:
            head = _clean_raw(str(title).split(":", 1)[0])
            if head and not _is_blocked_candidate(head, blocked):
                candidates.append(head)
                if " " in head:
                    candidates.append(_phrase_slug(head))
        label = clean_reference_label(title, url)
        if (
            label
            and len(label) <= 48
            and "..." not in label
            and not _is_blocked_candidate(label, blocked)
        ):
            candidates.append(label)
        match = _GITHUB_REPO_RE.search(url)
        if match:
            repo = match.group(2)
            if repo and not _is_blocked_candidate(repo, blocked):
                candidates.append(repo)
        host = (urlparse(url).netloc or "").lower()
        if "huggingface.co" in host:
            segment = urlparse(url).path.strip("/").split("/")[-1]
            if segment and not _is_blocked_candidate(segment, blocked):
                candidates.append(segment)

    for raw in _BOLD_RE.findall(summary):
        if len(raw) > 45 or len(raw.split()) > 5:
            continue
        if not _is_blocked_candidate(raw, blocked):
            candidates.append(raw)
            if " " in raw:
                candidates.append(_phrase_slug(raw))

    for raw in (
        _CODE_RE.findall(summary)
        + _CAMEL_RE.findall(summary)
        + _HYPHEN_NAME_RE.findall(summary)
    ):
        if len(raw) > 45:
            continue
        if not _is_blocked_candidate(raw, blocked):
            candidates.append(raw)

    for raw in _LINK_TEXT_RE.findall(summary):
        if len(raw) > 45 or "http" in raw.lower():
            continue
        if not _is_blocked_candidate(raw, blocked):
            candidates.append(raw)
            if " " in raw:
                candidates.append(_phrase_slug(raw))

    return candidates


def _keyword_priority(raw: str, data: dict[str, Any]) -> int:
    score = 0
    raw_l = raw.lower()
    for ref in data.get("referenced_urls") or []:
        title = str(ref.get("title") or "").lower()
        url = str(ref.get("url") or "").lower()
        if raw_l in title or raw_l in url:
            score += 12
    if _CAMEL_RE.fullmatch(raw.strip()):
        score += 4
    if "-" in raw and len(raw) <= 24:
        score += 2
    if len(raw) <= 16:
        score += 1
    return score


def curate_post_keywords(
    data: dict[str, Any],
    *,
    corpus: frozenset[str],
    topics_by_slug: dict[str, Topic],
) -> list[str]:
    """Normalized curated keywords for one post (excludes topic/hashtag duplicates)."""
    skip: set[str] = set()
    for tag in data.get("hashtags") or []:
        norm = normalize_index_term(str(tag), corpus)
        if norm:
            skip.add(norm)
    for slug in data.get("topics") or []:
        norm = normalize_topic_term(str(slug), corpus)
        if norm:
            skip.add(norm)

    best: dict[str, int] = {}
    for raw in collect_curated_raw_candidates(data):
        norm = normalize_index_term(raw, corpus)
        if not norm or norm in skip:
            continue
        if not is_acceptable_curated_keyword(norm):
            continue
        score = _keyword_priority(raw, data)
        best[norm] = max(best.get(norm, 0), score)

    ordered = sorted(best.keys(), key=lambda k: (-best[k], k))
    return ordered[:_MAX_KEYWORDS]


def _write_post_with_keywords(path: Path, data: dict[str, Any], keywords: list[str]) -> None:
    """Insert ``keywords`` after ``topics`` without changing other fields."""
    new_data: dict[str, Any] = {}
    for key, value in data.items():
        if key == "keywords":
            continue
        new_data[key] = value
        if key == "topics":
            new_data["keywords"] = keywords
    if "keywords" not in new_data:
        new_data["keywords"] = keywords
    path.write_text(json.dumps(new_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def backfill_keywords_in_tree(
    posts_root: Path,
    *,
    schema_path: Path,
    topics_path: Path,
    repo_root: Path,
) -> tuple[int, list[str]]:
    topics = load_topics(topics_path)
    topics_by_slug = {t.slug: t for t in topics}
    paths = discover_post_files(posts_root)
    records: list[PostRecord] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        records.append(PostRecord(path=path, data=data))

    corpus = build_index_corpus(records, topics_by_slug=topics_by_slug)
    validator = make_validator(schema_path)
    errors: list[str] = []

    for rec in records:
        keywords = curate_post_keywords(
            rec.data, corpus=corpus, topics_by_slug=topics_by_slug
        )
        _write_post_with_keywords(rec.path, rec.data, keywords)
        errors.extend(
            validate_post_file(rec.path, validator, repo_root=repo_root)
        )

    return len(paths), errors
