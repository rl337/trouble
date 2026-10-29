"""Discover post JSON files, validate against schema, and load records."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator

THUMBNAIL_PATTERN = re.compile(
    r"^posts/[0-9]{4}/[0-9]{2}/[0-9]{2}/[^/]+/media/[0-9]+\.webp$"
)


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
    def updated_at(self) -> datetime:
        return datetime.fromisoformat(self.data["updated_at"].replace("Z", "+00:00"))

    @property
    def day_key(self) -> str:
        """Archive day from file path (YYYY-MM-DD), not posted_at."""
        parts = self.path.parts
        idx = parts.index("posts")
        return f"{parts[idx + 1]}-{parts[idx + 2]}-{parts[idx + 3]}"

    @property
    def update_day_key(self) -> str:
        """Front-page grouping day from updated_at (UTC)."""
        return self.updated_at.strftime("%Y-%m-%d")

    @property
    def was_updated(self) -> bool:
        return self.data["updated_at"] != self.data["collected_at"]


def load_schema(schema_path: Path) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def make_validator(schema_path: Path) -> Draft202012Validator:
    schema = load_schema(schema_path)
    return Draft202012Validator(schema)


def discover_post_files(posts_root: Path) -> list[Path]:
    if not posts_root.is_dir():
        return []
    return sorted(posts_root.glob("*/*/*/*.json"))


def resolve_repo_asset(repo_root: Path, repo_relative: str) -> Path:
    direct = repo_root / repo_relative
    if direct.is_file():
        return direct
    fixture_mirror = repo_root / "sample" / "fixtures" / "media-assets" / repo_relative
    return fixture_mirror


def _validate_media_and_dates(
    path: Path,
    data: dict[str, Any],
    repo_root: Path,
) -> list[str]:
    errors: list[str] = []
    post_id = str(data.get("id", ""))

    collected = data.get("collected_at")
    updated = data.get("updated_at")
    if collected and updated:
        try:
            c_dt = datetime.fromisoformat(str(collected).replace("Z", "+00:00"))
            u_dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
            if u_dt < c_dt:
                errors.append(f"{path}: updated_at must be >= collected_at")
        except ValueError:
            pass

    for idx, item in enumerate(data.get("media") or []):
        media_type = item.get("type")
        thumb = item.get("thumbnail")
        if thumb:
            if media_type != "image":
                errors.append(
                    f"{path}: media[{idx}].thumbnail allowed only for type image, got {media_type!r}"
                )
            if not THUMBNAIL_PATTERN.match(thumb):
                errors.append(f"{path}: media[{idx}].thumbnail invalid path: {thumb!r}")
            elif f"/{post_id}/media/" not in thumb:
                errors.append(
                    f"{path}: media[{idx}].thumbnail must live under posts/.../{post_id}/media/"
                )
            else:
                asset = resolve_repo_asset(repo_root, thumb)
                if not asset.is_file():
                    errors.append(f"{path}: media[{idx}].thumbnail file not found: {thumb}")

        if item.get("ocr_text") and media_type not in ("image", "gif"):
            errors.append(f"{path}: media[{idx}].ocr_text only applies to image or gif")

    return errors


def validate_post_file(
    path: Path,
    validator: Draft202012Validator,
    *,
    repo_root: Path | None = None,
) -> list[str]:
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

    if not errors and repo_root is not None:
        errors.extend(_validate_media_and_dates(path, data, repo_root))

    return errors


def validate_all_posts(
    posts_root: Path,
    schema_path: Path,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    validator = make_validator(schema_path)
    root = repo_root or posts_root.parent
    all_errors: list[str] = []
    for path in discover_post_files(posts_root):
        all_errors.extend(validate_post_file(path, validator, repo_root=root))
    return all_errors


def load_posts(posts_root: Path, schema_path: Path, *, repo_root: Path | None = None) -> list[PostRecord]:
    errors = validate_all_posts(posts_root, schema_path, repo_root=repo_root)
    if errors:
        raise ValueError("Post validation failed:\n" + "\n".join(errors))

    records: list[PostRecord] = []
    for path in discover_post_files(posts_root):
        data = json.loads(path.read_text(encoding="utf-8"))
        records.append(PostRecord(path=path, data=data))

    records.sort(key=lambda r: (r.updated_at, r.id), reverse=True)
    return records


def validate_json_files(
    paths: list[Path],
    schema_path: Path,
    *,
    repo_root: Path | None = None,
) -> list[str]:
    validator = make_validator(schema_path)
    root = repo_root or (paths[0].parent if paths else Path("."))
    all_errors: list[str] = []
    for path in paths:
        all_errors.extend(validate_post_file(path, validator, repo_root=root))
    return all_errors
