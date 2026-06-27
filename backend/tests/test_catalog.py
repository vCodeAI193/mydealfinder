"""Unit tests for the catalog keyword matching."""
from app.sources.catalog import find_items


def test_find_items_matches_brand():
    items = find_items("sony")
    assert any(i.slug == "sony-wh-1000xm5" for i in items)


def test_find_items_is_case_insensitive():
    assert find_items("SONY") == find_items("sony")


def test_find_items_requires_all_tokens():
    # "apple headphones" should match AirPods (apple + headphones keyword)
    slugs = {i.slug for i in find_items("apple headphones")}
    assert "apple-airpods-pro-2" in slugs
    # ...but not the iPhone, which is not tagged as headphones.
    assert "apple-iphone-15" not in slugs


def test_find_items_empty_query_returns_nothing():
    assert find_items("   ") == []


def test_find_items_no_match():
    assert find_items("nonexistentproductxyz") == []


def test_fuzzy_matches_typo_when_enabled():
    # "sny" is a typo for "sony"; only matches with fuzzy on (F001).
    assert find_items("sny") == []
    slugs = {i.slug for i in find_items("sny", fuzzy=True)}
    assert "sony-wh-1000xm5" in slugs


def test_fuzzy_still_requires_reasonable_similarity():
    # Gibberish must not match even with fuzzy enabled.
    assert find_items("zzzzzz", fuzzy=True) == []
