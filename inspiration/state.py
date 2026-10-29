"""Load and validate ingestion run state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator

from inspiration.posts import discover_post_files


def load_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def derive_ingested_post_ids(posts_root: Path) -> list[str]:
    return [p.stem for p in discover_post_files(posts_root)]


def validate_state_file(
    state_path: Path,
    schema_path: Path,
    posts_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if not state_path.is_file():
        return [f"{state_path}: missing run-state file"]

    try:
        data = load_state(state_path)
    except json.JSONDecodeError as exc:
        return [f"{state_path}: invalid JSON: {exc}"]

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: e.path):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{state_path}: {loc}: {err.message}")

    if posts_root and not errors:
        on_disk = set(derive_ingested_post_ids(posts_root))
        listed = set(data.get("ingested_post_ids") or [])
        missing = on_disk - listed
        if missing:
            errors.append(
                f"{state_path}: ingested_post_ids missing ids present under posts/: "
                f"{sorted(missing)!r} (sync ids after ingest)"
            )

    return errors
