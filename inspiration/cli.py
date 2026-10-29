"""CLI entrypoints for validate and build."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from inspiration.media_assets import (
    copy_fixture_media_assets,
    copy_post_media_to_site,
    stage_post_media_for_sphinx,
)
from inspiration.posts import load_posts, validate_all_posts, validate_json_files
from inspiration.sitegen import generate_sphinx_sources
from inspiration.state import validate_state_file
from inspiration.topics import load_topics

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POSTS = REPO_ROOT / "posts"
DEFAULT_SCHEMA = REPO_ROOT / "schema" / "post.schema.json"
DEFAULT_STATE_SCHEMA = REPO_ROOT / "schema" / "last_run.schema.json"
DEFAULT_STATE = REPO_ROOT / "state" / "last_run.json"
DEFAULT_TOPICS = REPO_ROOT / "topics.yaml"
SPHINX_CONF_DIR = REPO_ROOT / "sphinx"
GENERATED = REPO_ROOT / ".build" / "sources"
HTML_OUT = REPO_ROOT / ".build" / "html"


def cmd_validate(args: argparse.Namespace) -> int:
    schema = Path(args.schema)
    errors: list[str] = []

    if args.fixtures:
        fixture_paths = sorted(Path(args.fixtures).glob("*.json"))
        errors.extend(
            validate_json_files(fixture_paths, schema, repo_root=REPO_ROOT)
        )

    posts_root = Path(args.posts)
    errors.extend(
        validate_all_posts(posts_root, schema, repo_root=REPO_ROOT)
    )

    state_path = Path(args.state)
    errors.extend(
        validate_state_file(
            state_path,
            Path(args.state_schema),
            posts_root=posts_root,
        )
    )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("All posts valid.")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    posts_root = Path(args.posts)
    schema = Path(args.schema)
    topics_path = Path(args.topics)

    records = load_posts(posts_root, schema, repo_root=REPO_ROOT)
    topics = load_topics(topics_path)
    generate_sphinx_sources(records=records, topics=topics, out_dir=GENERATED)
    stage_post_media_for_sphinx(posts_root, GENERATED)

    if HTML_OUT.exists():
        shutil.rmtree(HTML_OUT)
    HTML_OUT.mkdir(parents=True)
    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-c",
        str(SPHINX_CONF_DIR),
        "-b",
        "html",
        str(GENERATED),
        str(HTML_OUT),
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        return result.returncode

    copy_post_media_to_site(posts_root, HTML_OUT)
    copy_fixture_media_assets(REPO_ROOT, HTML_OUT)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inspiration", description="Inspiration blog builder")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="Validate post JSON against schema")
    p_val.add_argument("--posts", default=str(DEFAULT_POSTS))
    p_val.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    p_val.add_argument("--state", default=str(DEFAULT_STATE))
    p_val.add_argument("--state-schema", default=str(DEFAULT_STATE_SCHEMA))
    p_val.add_argument(
        "--fixtures",
        default=str(REPO_ROOT / "sample" / "fixtures"),
        help="Also validate fixture JSON files",
    )
    p_val.set_defaults(func=cmd_validate)

    p_build = sub.add_parser("build", help="Validate posts and build Sphinx HTML")
    p_build.add_argument("--posts", default=str(DEFAULT_POSTS))
    p_build.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    p_build.add_argument("--topics", default=str(DEFAULT_TOPICS))
    p_build.set_defaults(func=cmd_build)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
