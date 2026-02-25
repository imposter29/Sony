"""
utils.py — Shared helpers: HTML cleaning, URL normalization, field sanitization.
"""

import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


BASE = "https://www.sony.co.in"


def clean_text(raw) -> str | None:
    """Strip HTML tags and collapse whitespace. Returns None for empty strings."""
    if raw is None:
        return None
    if hasattr(raw, "get_text"):
        text = raw.get_text(separator=" ", strip=True)
    else:
        text = BeautifulSoup(str(raw), "lxml").get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else None


def normalize_url(href: str, base: str = BASE) -> str | None:
    """Resolve relative URLs to absolute. Returns None for empty/invalid hrefs."""
    if not href:
        return None
    href = href.strip()
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("http"):
        return href
    return urljoin(base, href)


def normalize_price(raw: str | None) -> str | None:
    """Strip currency symbols, commas; return numeric string or None."""
    if not raw:
        return None
    cleaned = re.sub(r"[₹,\s]", "", str(raw)).strip()
    return cleaned if cleaned else None


def extract_model_from_url(url: str) -> str | None:
    """
    Try to infer product model number from the URL slug.
    Sony product URLs typically end with the model code e.g. /ilce-7m4
    """
    path = urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1]
    # Remove query strings and common suffixes
    slug = re.sub(r"[?#].*", "", slug)
    return slug.upper() if slug else None


def dedupe_images(urls: list) -> list:
    """Deduplicate image URLs while preserving order."""
    seen = set()
    out = []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def resolve_image_url(src: str | None) -> str | None:
    """Upgrade thumbnail URLs to high-res if Sony follows a known pattern."""
    if not src:
        return None
    # Sony CDN: swap thumbnail size parameters for larger version
    src = re.sub(r"\?.*$", "", src)      # strip query params
    src = src.replace("/S/", "/L/")       # small → large
    src = src.replace("_S.", "_L.")
    src = src.replace("-S.", "-L.")
    return normalize_url(src)


def make_empty_product(category: str, sub_category: str | None, url: str) -> dict:
    """Return a skeleton product dict with all required fields set to None."""
    return {
        "productId": None,
        "productName": None,
        "brand": "Sony",
        "category": category,
        "subCategory": sub_category,
        "price": None,
        "mrp": None,
        "currency": "INR",
        "shortDescription": None,
        "fullDescription": None,
        "features": [],
        "specifications": {},
        "images": [],
        "warranty": None,
        "boxContents": None,
        "manuals": [],
        "compatibleProducts": [],
        "productUrl": url,
    }
