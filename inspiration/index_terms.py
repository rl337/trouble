"""Deterministic extraction and normalization of Sphinx genindex terms."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from inspiration.topics import Topic

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

# Do not singularize or alter these tokens.
_TERM_EXCEPTIONS = frozenset(
    {
        "mcp",
        "kubernetes",
        "gpu",
        "news",
        "analysis",
        "status",
        "focus",
        "canvas",
        "alias",
        "atlas",
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
_GITHUB_REPO_RE = re.compile(r"github\.com/([^/]+)/([^/#?]+)")
_HANDLE_RE = re.compile(r"^@?[a-z0-9_]{1,30}$", re.I)


def _clean_raw(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip(".,;:!?\"'()[]")


def is_username_like(term: str) -> bool:
    """True for @handles and underscore-style account names (not plain words)."""
    t = term.strip()
    if t.startswith("@"):
        return True
    tl = t.lstrip("@").lower()
    if "_" in tl and _HANDLE_RE.match(tl):
        return True
    return False


def singularize_token(token: str, corpus: frozenset[str] | None) -> str:
    if token in _TERM_EXCEPTIONS:
        return token
    if token.endswith("ies") and len(token) > 4:
        candidate = token[:-3] + "y"
        if corpus is None or candidate in corpus or len(candidate) >= 3:
            return candidate
    if token.endswith("is") and len(token) > 4:
        return token
    if token.endswith("us") and len(token) > 3:
        candidate = token[:-1]
        if corpus is not None and candidate in corpus:
            return candidate
        return token
    if (
        token.endswith("s")
        and not token.endswith("ss")
        and len(token) > 3
    ):
        candidate = token[:-1]
        if corpus is None or candidate in corpus or len(candidate) >= 3:
            return candidate
    return token


def normalize_index_term(raw: str, corpus: frozenset[str] | None = None) -> str | None:
    """
    Shared normalization for hashtags, keywords, topics, and noun singles.

    Strips leading '#', lowercases, and singularizes when safe or corpus-supported.
    Returns None when the term should not be indexed.
    """
    term = _clean_raw(str(raw)).lstrip("#").lower()
    if not term:
        return None
    if is_username_like(term):
        return None
    term = term.replace("_", "")
    if term in _STOPWORDS:
        return None
    if len(term) < 2 or len(term) > 80:
        return None

    # Hyphenated slugs: singularize each segment, rejoin.
    if "-" in term:
        parts = [singularize_token(p, corpus) for p in term.split("-") if p]
        term = "-".join(parts) if parts else term
    else:
        term = singularize_token(term, corpus)

    if not term or is_username_like(term):
        return None
    return term


def normalize_topic_term(slug: str, corpus: frozenset[str] | None) -> str | None:
    parts = slug.lower().replace("_", "-").split("-")
    parts = [singularize_token(p, corpus) for p in parts if p]
    if not parts:
        return None
    return "-".join(parts)


def clean_reference_label(title: str | None, url: str) -> str | None:
    """Strip noisy link titles down to repo/model names."""
    if title:
        t = _clean_raw(title)
        gh = re.match(r"GitHub\s*-\s*([^:]+)(?::|$)", t, flags=re.I)
        if gh:
            t = gh.group(1).strip()
        if " · Hugging Face" in t:
            t = t.split("·", 1)[0].strip()
        if t.lower().startswith("x ·"):
            t = t.split("·", 1)[-1].strip()
        # Drop trailing "(fixture)" noise in tests/docs.
        t = re.sub(r"\s*\([^)]*fixture[^)]*\)\s*$", "", t, flags=re.I).strip()
        t = re.sub(r"\s*\([^)]*$", "", t).strip()
        if "/" in t and t.count("/") == 1 and not t.startswith("http"):
            # owner/repo title -> repo only (avoid bare owner handles in index)
            t = t.split("/", 1)[1]
        return t or None

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    path = parsed.path.strip("/")
    if "github.com" in host and path:
        parts = path.split("/")
        if len(parts) >= 2:
            return parts[1]
        return None
    if "huggingface.co" in host and path:
        return path.split("/")[-1]
    last = path.split("/")[-1] if path else ""
    if last and "." not in last:
        return last.replace("-", " ")
    return None


def _author_blocklist(data: dict[str, Any]) -> set[str]:
    author = data.get("author") or {}
    blocked: set[str] = set()
    name = str(author.get("name", "")).strip().lower()
    handle = str(author.get("handle", "")).lstrip("@").strip().lower()
    if name:
        blocked.add(name)
        for part in name.split():
            blocked.add(part)
    if handle:
        blocked.add(handle)
        blocked.add(f"@{handle}")
    return blocked


def _is_blocked_candidate(raw: str, blocked: set[str]) -> bool:
    t = _clean_raw(raw).lower()
    if not t:
        return True
    if t in blocked:
        return True
    for b in blocked:
        if len(b) >= 4 and b in t:
            return True
    if t.lstrip("@") in blocked:
        return True
    if "@" in t and is_username_like(t):
        return True
    # Skip summary attribution blobs like "Name (@handle)"
    if re.search(r"@\w+", t) and len(t) < 80:
        return True
    return False


def collect_raw_noun_candidates(data: dict[str, Any]) -> list[str]:
    blocked = _author_blocklist(data)
    candidates: list[str] = []

    summary = str(data.get("summary_md", ""))
    for raw in (
        _BOLD_RE.findall(summary)
        + _CODE_RE.findall(summary)
        + _LINK_TEXT_RE.findall(summary)
        + _CAMEL_RE.findall(summary)
        + _HYPHEN_NAME_RE.findall(summary)
        + _CAP_PHRASE_RE.findall(summary)
    ):
        if not _is_blocked_candidate(raw, blocked):
            candidates.append(raw)

    for ref in data.get("referenced_urls") or []:
        url = str(ref.get("url", ""))
        label = clean_reference_label(ref.get("title"), url)
        if label and not _is_blocked_candidate(label, blocked):
            candidates.append(label)
        match = _GITHUB_REPO_RE.search(url)
        if match:
            repo = match.group(2)
            if repo and not _is_blocked_candidate(repo, blocked):
                candidates.append(repo)

    return candidates


def collect_raw_terms_for_post(
    data: dict[str, Any],
    *,
    topics_by_slug: dict[str, Topic],
) -> list[str]:
    raw: list[str] = []
    for tag in data.get("hashtags") or []:
        raw.append(str(tag))
    for slug in data.get("topics") or []:
        raw.append(str(slug))
        topic = topics_by_slug.get(str(slug))
        if topic:
            raw.append(topic.title)
    if "keywords" in data:
        raw.extend(str(k) for k in data["keywords"])
    else:
        raw.extend(collect_raw_noun_candidates(data))
    return raw


def build_index_corpus(
    records: list[Any],
    *,
    topics_by_slug: dict[str, Topic],
) -> frozenset[str]:
    """Corpus of normalized tokens (pre-singularization pass) for plural collapse."""
    tokens: set[str] = set()
    for rec in records:
        data = rec.data if hasattr(rec, "data") else rec
        for raw in collect_raw_terms_for_post(data, topics_by_slug=topics_by_slug):
            base = _clean_raw(str(raw)).lstrip("#").lower().replace("_", "")
            if not base or is_username_like(base):
                continue
            tokens.add(base)
            if "-" in base:
                tokens.update(p for p in base.split("-") if p)
    return frozenset(tokens)


def normalized_index_terms_for_post(
    data: dict[str, Any],
    *,
    topics_by_slug: dict[str, Topic],
    corpus: frozenset[str],
) -> list[str]:
    """Unique normalized ``single:`` index terms for one post."""
    seen: set[str] = set()
    ordered: list[str] = []

    def add_raw(raw: str) -> None:
        norm = normalize_index_term(raw, corpus)
        if norm and norm not in seen:
            seen.add(norm)
            ordered.append(norm)

    for tag in data.get("hashtags") or []:
        add_raw(str(tag))

    for slug in data.get("topics") or []:
        topic_norm = normalize_topic_term(str(slug), corpus)
        if topic_norm:
            if topic_norm not in seen:
                seen.add(topic_norm)
                ordered.append(topic_norm)

    if "keywords" in data:
        for kw in data["keywords"]:
            add_raw(str(kw))
    else:
        for raw in collect_raw_noun_candidates(data):
            add_raw(raw)

    return ordered


def build_post_index_lines(
    data: dict[str, Any],
    *,
    topics_by_slug: dict[str, Topic],
    corpus: frozenset[str],
) -> list[str]:
    terms = normalized_index_terms_for_post(
        data, topics_by_slug=topics_by_slug, corpus=corpus
    )
    return [f"   single: {term}" for term in terms]


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
