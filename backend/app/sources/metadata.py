"""Static, per-source metadata used for display enrichments.

Kept separate from the sources themselves so a real scraper can reuse the same
trust ratings without duplicating them.
"""

# F014: a static trust/reliability rating per source (0–5).
SOURCE_RATINGS: dict[str, float] = {
    "amazon": 4.6,
    "ebay": 3.9,
    "walmart": 4.3,
}


def rating_for(source: str) -> float | None:
    return SOURCE_RATINGS.get(source.lower())
