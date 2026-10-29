from pathlib import Path

from inspiration.posts import validate_json_files

REPO = Path(__file__).resolve().parents[1]
SCHEMA = REPO / "schema" / "post.schema.json"
FIXTURES = REPO / "sample" / "fixtures"


def test_fixture_posts_validate_against_schema():
    paths = sorted(FIXTURES.glob("*.json"))
    assert len(paths) >= 2
    errors = validate_json_files(paths, SCHEMA)
    assert errors == [], errors


def test_empty_posts_directory_validates():
    from inspiration.posts import validate_all_posts

    errors = validate_all_posts(REPO / "posts", SCHEMA)
    assert errors == []
