"""A small, deterministic demo catalog shared by the mock sources.

Each product has a base price; individual sources apply a stable multiplier so
the same product shows different prices per source (enabling real comparison).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogItem:
    slug: str
    name: str
    brand: str
    category: str
    description: str
    base_price: float
    image_url: str
    keywords: tuple[str, ...]


CATALOG: tuple[CatalogItem, ...] = (
    CatalogItem(
        slug="sony-wh-1000xm5",
        name="Sony WH-1000XM5 Wireless Headphones",
        brand="Sony",
        category="Audio",
        description="Industry-leading noise-cancelling over-ear headphones with 30h battery life.",
        base_price=349.99,
        image_url="https://picsum.photos/seed/sony-wh-1000xm5/400/400",
        keywords=("sony", "headphones", "noise", "cancelling", "wh-1000xm5", "audio", "wireless"),
    ),
    CatalogItem(
        slug="apple-airpods-pro-2",
        name="Apple AirPods Pro (2nd generation)",
        brand="Apple",
        category="Audio",
        description="Active noise cancellation, adaptive transparency, and USB-C charging case.",
        base_price=249.00,
        image_url="https://picsum.photos/seed/airpods-pro-2/400/400",
        keywords=("apple", "airpods", "pro", "earbuds", "audio", "wireless", "headphones"),
    ),
    CatalogItem(
        slug="samsung-galaxy-s24",
        name="Samsung Galaxy S24 (256GB)",
        brand="Samsung",
        category="Phones",
        description="6.2-inch flagship Android phone with Galaxy AI and a triple camera system.",
        base_price=799.99,
        image_url="https://picsum.photos/seed/galaxy-s24/400/400",
        keywords=("samsung", "galaxy", "s24", "phone", "android", "smartphone"),
    ),
    CatalogItem(
        slug="apple-iphone-15",
        name="Apple iPhone 15 (128GB)",
        brand="Apple",
        category="Phones",
        description="6.1-inch Super Retina XDR display, A16 Bionic, USB-C, 48MP main camera.",
        base_price=799.00,
        image_url="https://picsum.photos/seed/iphone-15/400/400",
        keywords=("apple", "iphone", "15", "phone", "ios", "smartphone"),
    ),
    CatalogItem(
        slug="dell-xps-13",
        name="Dell XPS 13 Laptop (i7, 16GB, 512GB)",
        brand="Dell",
        category="Laptops",
        description="Compact 13-inch ultrabook with InfinityEdge display and 12th-gen Intel Core i7.",
        base_price=1199.00,
        image_url="https://picsum.photos/seed/dell-xps-13/400/400",
        keywords=("dell", "xps", "laptop", "notebook", "ultrabook", "computer"),
    ),
    CatalogItem(
        slug="logitech-mx-master-3s",
        name="Logitech MX Master 3S Mouse",
        brand="Logitech",
        category="Accessories",
        description="Ergonomic wireless mouse with 8K DPI tracking and quiet clicks.",
        base_price=99.99,
        image_url="https://picsum.photos/seed/mx-master-3s/400/400",
        keywords=("logitech", "mx", "master", "mouse", "accessories", "wireless"),
    ),
    CatalogItem(
        slug="nintendo-switch-oled",
        name="Nintendo Switch OLED",
        brand="Nintendo",
        category="Gaming",
        description="7-inch OLED screen, enhanced audio, and 64GB internal storage.",
        base_price=349.99,
        image_url="https://picsum.photos/seed/switch-oled/400/400",
        keywords=("nintendo", "switch", "oled", "gaming", "console"),
    ),
    CatalogItem(
        slug="kindle-paperwhite",
        name="Amazon Kindle Paperwhite (16GB)",
        brand="Amazon",
        category="E-readers",
        description="6.8-inch glare-free display, adjustable warm light, weeks of battery life.",
        base_price=149.99,
        image_url="https://picsum.photos/seed/kindle-paperwhite/400/400",
        keywords=("amazon", "kindle", "paperwhite", "ereader", "ebook", "reader"),
    ),
)


def find_items(keyword: str) -> list[CatalogItem]:
    """Return catalog items whose name or keywords match `keyword`.

    Matching is case-insensitive and token-based: every whitespace-separated
    token in the query must appear in the item's searchable text.
    """
    query = keyword.strip().lower()
    if not query:
        return []
    tokens = query.split()
    matches: list[CatalogItem] = []
    for item in CATALOG:
        haystack = " ".join((item.name.lower(), item.brand.lower(), item.category.lower(), *item.keywords))
        if all(token in haystack for token in tokens):
            matches.append(item)
    return matches
