"""Load topics.yaml and validate topic slugs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Topic:
    slug: str
    title: str
    description: str


def load_topics(topics_path: Path) -> list[Topic]:
    raw: Any = yaml.safe_load(topics_path.read_text(encoding="utf-8"))
    entries = raw.get("topics", raw) if isinstance(raw, dict) else raw
    topics: list[Topic] = []
    for item in entries:
        topics.append(
            Topic(
                slug=item["slug"],
                title=item["title"],
                description=str(item["description"]).strip(),
            )
        )
    return topics


def topics_by_slug(topics_path: Path) -> dict[str, Topic]:
    return {t.slug: t for t in load_topics(topics_path)}
