from pathlib import Path

from inspiration.posts import validate_all_posts, validate_json_files
from inspiration.state import validate_state_file

REPO = Path(__file__).resolve().parents[1]
SCHEMA = REPO / "schema" / "post.schema.json"
STATE_SCHEMA = REPO / "schema" / "last_run.schema.json"
FIXTURES = REPO / "sample" / "fixtures"


def test_fixture_posts_validate_against_schema():
    paths = sorted(FIXTURES.glob("*.json"))
    assert len(paths) >= 2
    errors = validate_json_files(paths, SCHEMA, repo_root=REPO)
    assert errors == [], errors


def test_empty_posts_directory_validates():
    errors = validate_all_posts(REPO / "posts", SCHEMA, repo_root=REPO)
    assert errors == []


def test_run_state_validates():
    errors = validate_state_file(
        REPO / "state" / "last_run.json",
        STATE_SCHEMA,
        posts_root=REPO / "posts",
    )
    assert errors == [], errors
