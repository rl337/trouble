"""Discover post JSON files, validate against schema, and load records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class PostRecord:
    path: Path
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.data["id"])

    @property
    def posted_at(self) -> datetime:
        return datetime.fromisoformat(self.data["posted_at"].replace("Z", "+00:00"))

    @property
    def day_key(self) -> str:
        """Archive day from file path (YYYY/MM/DD), not posted_at."""
        parts = self.path.parts
        # .../posts/YYYY/MM/DD/id.json
        idx = parts.index("posts")
        return f"{parts[idx + 1]}-{parts[idx + 2]}-{parts[idx + 3]}"


def load_schema(schema_path: Path) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def make_validator(schema_path: Path) -> Draft202012Validator:
    schema = load_schema(schema_path)
    return Draft202012Validator(schema)


def discover_post_files(posts_root: Path) -> list[Path]:
    if not posts_root.is_dir():
        return []
    files = sorted(posts_root.glob("*/*/*/*.json"))
    return files


def validate_post_file(path: Path, validator: Draft202012Validator) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"]

    for err in sorted(validator.iter_errors(data), key=lambda e: e.path):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{path}: {loc}: {err.message}")

    expected_id = path.stem
    if not errors and str(data.get("id")) != expected_id:
        errors.append(f"{path}: id field {data.get('id')!r} must match filename {expected_id}")

    return errors


def validate_all_posts(posts_root: Path, schema_path: Path) -> list[str]:
    validator = make_validator(schema_path)
    all_errors: list[str] = []
    for path in discover_post_files(posts_root):
        all_errors.extend(validate_post_file(path, validator))
    return all_errors


def load_posts(posts_root: Path, schema_path: Path) -> list[PostRecord]:
    errors = validate_all_posts(posts_root, schema_path)
    if errors:
        raise ValueError("Post validation failed:\n" + "\n".join(errors))

    records: list[PostRecord] = []
    for path in discover_post_files(posts_root):
        data = json.loads(path.read_text(encoding="utf-8"))
        records.append(PostRecord(path=path, data=data))

    records.sort(key=lambda r: (r.posted_at, r.id), reverse=True)
    return records


def validate_json_files(paths: list[Path], schema_path: Path) -> list[str]:
    validator = make_validator(schema_path)
    all_errors: list[str] = []
    for path in paths:
        all_errors.extend(validate_post_file(path, validator))
    return all_errors
