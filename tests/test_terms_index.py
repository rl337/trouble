from inspiration.terms_index import slug_for_term


def test_slug_disambiguates_collisions():
    owner: dict[str, str] = {}
    assert slug_for_term("a/b", owner) == "a-b"
    assert slug_for_term("a-b", owner) == "a-b-2"
