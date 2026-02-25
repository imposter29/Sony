"""
detail_scraper.py — Extracts all product fields from a single Sony product detail page.
"""

import json
import logging
import re
from bs4 import BeautifulSoup, Tag

from browser import fetch_page, random_delay
from utils import (
    clean_text, normalize_url, normalize_price,
    extract_model_from_url, dedupe_images, resolve_image_url, make_empty_product,
)

logger = logging.getLogger(__name__)
BASE = "https://www.sony.co.in"


# ──────────────────────────────────────────────────────────────────────────────
# Helper: try multiple CSS selectors, return first non-empty text
# ──────────────────────────────────────────────────────────────────────────────

def _first_text(soup: BeautifulSoup, *selectors: str) -> str | None:
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = clean_text(el)
            if text:
                return text
    return None


def _first_attr(soup: BeautifulSoup, attr: str, *selectors: str) -> str | None:
    for sel in selectors:
        el = soup.select_one(sel)
        if el and el.get(attr):
            return el[attr].strip()
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Extraction helpers
# ──────────────────────────────────────────────────────────────────────────────

def _extract_product_id(soup: BeautifulSoup, url: str) -> str | None:
    # 1. JSON-LD structured data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") in ("Product",):
                    sku = item.get("sku") or item.get("productID") or item.get("mpn")
                    if sku:
                        return str(sku).upper().strip()
        except Exception:
            pass

    # 2. meta tags
    for name in ("product-id", "og:product_id", "sku"):
        el = soup.find("meta", attrs={"name": name}) or soup.find("meta", property=name)
        if el and el.get("content"):
            return el["content"].strip().upper()

    # 3. data attributes on body / product container
    for attr in ("data-product-id", "data-sku", "data-model"):
        el = soup.find(attrs={attr: True})
        if el:
            return el[attr].strip().upper()

    # 4. fall back to URL slug
    return extract_model_from_url(url)


def _extract_price(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Returns (price, mrp)."""
    price_selectors = [
        ".product-price__current",
        ".price-current",
        "[data-testid='current-price']",
        ".pdp-price__current-price",
        ".product-price",
        ".price",
        "span.pdp-header__price",
        ".product-detail-price",
    ]
    mrp_selectors = [
        ".product-price__original",
        ".price-original",
        "[data-testid='original-price']",
        ".pdp-price__original-price",
        ".price--compare",
        "span.price-original",
    ]
    # Also try JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    offers = item.get("offers", {})
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    price = normalize_price(str(offers.get("price", "")))
                    if price:
                        return price, None
        except Exception:
            pass

    price = normalize_price(_first_text(soup, *price_selectors))
    mrp = normalize_price(_first_text(soup, *mrp_selectors))
    return price, mrp


def _extract_descriptions(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    short_selectors = [
        ".product-description__short",
        ".pdp-header__short-desc",
        ".product-title-desc",
        "meta[name='description']",
        "meta[property='og:description']",
    ]
    full_selectors = [
        ".product-description__full",
        ".pdp-description",
        ".product-overview",
        ".product-details__description",
        "#description",
        ".description",
    ]
    # meta tag values use 'content' attr
    short = None
    for sel in short_selectors:
        el = soup.select_one(sel)
        if el:
            val = el.get("content") or clean_text(el)
            if val:
                short = val
                break

    full = _first_text(soup, *full_selectors)
    return short, full


def _extract_features(soup: BeautifulSoup) -> list[str]:
    selectors = [
        ".product-features__list li",
        ".pdp-features li",
        ".feature-list li",
        ".highlights li",
        ".key-features li",
        "ul.feature-bullets li",
        ".product-highlights__list li",
        ".features-overview li",
    ]
    for sel in selectors:
        items = soup.select(sel)
        if items:
            feats = [clean_text(i) for i in items]
            feats = [f for f in feats if f]
            if feats:
                return feats
    return []


def _extract_specifications(soup: BeautifulSoup) -> dict:
    specs: dict = {}

    # Strategy 1: spec tables (th/td pairs)
    for table in soup.select("table.spec-table, table.specifications, table, .spec-list"):
        rows = table.select("tr")
        for row in rows:
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                key = clean_text(cells[0])
                val = clean_text(cells[1])
                if key and val:
                    specs[key] = val

    # Strategy 2: definition lists (<dl><dt>key</dt><dd>val</dd></dl>)
    for dl in soup.select("dl.spec-list, dl.specifications, dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        for dt, dd in zip(dts, dds):
            key = clean_text(dt)
            val = clean_text(dd)
            if key and val:
                specs[key] = val

    # Strategy 3: JSON-LD additionalProperty
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    for prop in item.get("additionalProperty", []):
                        name = prop.get("name")
                        val = prop.get("value")
                        if name and val:
                            specs[str(name)] = str(val)
        except Exception:
            pass

    # Strategy 4: key-value divs/spans with common class patterns
    for container in soup.select(
        ".spec-item, .specification-item, .pdp-spec__item, .spec-row"
    ):
        key_el = container.select_one(".spec-label, .spec-name, .key, dt")
        val_el = container.select_one(".spec-value, .value, dd")
        key = clean_text(key_el) if key_el else None
        val = clean_text(val_el) if val_el else None
        if key and val:
            specs[key] = val

    return specs


def _extract_images(soup: BeautifulSoup, url: str) -> list[str]:
    imgs: list[str] = []

    # Primary: og:image meta
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        imgs.append(resolve_image_url(og["content"]))

    # Product gallery / carousel images
    gallery_selectors = [
        ".product-gallery img",
        ".pdp-gallery img",
        ".product-images img",
        ".product-thumbnail img",
        ".carousel img",
        "img[data-role='product-image']",
        "img.product-image",
        "img[data-src]",
        ".swiper-slide img",
        ".gallery-slide img",
    ]
    for sel in gallery_selectors:
        for img in soup.select(sel):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            resolved = resolve_image_url(src)
            if resolved:
                imgs.append(resolved)

    # JSON-LD image
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") == "Product":
                    img_field = item.get("image")
                    if isinstance(img_field, list):
                        for i in img_field:
                            imgs.append(resolve_image_url(str(i)))
                    elif isinstance(img_field, str):
                        imgs.append(resolve_image_url(img_field))
        except Exception:
            pass

    return dedupe_images([i for i in imgs if i])


def _extract_warranty(soup: BeautifulSoup) -> str | None:
    selectors = [
        ".warranty",
        ".product-warranty",
        "[data-component='Warranty']",
        "#warranty",
        ".pdp-warranty",
    ]
    # Also search text nodes containing "warranty"
    text = _first_text(soup, *selectors)
    if text:
        return text
    # Fallback: find any element whose text mentions warranty
    for el in soup.find_all(text=re.compile(r"warranty", re.I)):
        parent = el.parent
        if parent and parent.name not in ("script", "style"):
            t = clean_text(parent)
            if t and len(t) < 200:
                return t
    return None


def _extract_box_contents(soup: BeautifulSoup) -> str | None:
    selectors = [
        ".box-contents",
        ".in-the-box",
        ".whats-in-box",
        "#in-the-box",
        ".package-contents",
        ".pdp-box-contents",
    ]
    return _first_text(soup, *selectors)


def _extract_manuals(soup: BeautifulSoup) -> list[str]:
    manuals = []
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        text = (a.get_text() or "").lower()
        if any(kw in href or kw in text for kw in ("manual", "guide", "pdf", "download")):
            full = normalize_url(a["href"])
            if full:
                manuals.append(full)
    return list(dict.fromkeys(manuals))   # dedupe


def _extract_compatible_products(soup: BeautifulSoup) -> list[str]:
    results = []
    sections = soup.select(
        ".compatible-products, .accessories, .related-products, .you-may-also-like"
    )
    for section in sections:
        for a in section.find_all("a", href=True):
            name = clean_text(a)
            if name:
                results.append(name)
    return list(dict.fromkeys(results))


# ──────────────────────────────────────────────────────────────────────────────
# Main public function
# ──────────────────────────────────────────────────────────────────────────────

async def scrape_product(
    page,
    url: str,
    category: str,
    sub_category: str | None,
) -> dict:
    """
    Scrape a single product detail page.
    Returns a product dict with all required fields.
    """
    product = make_empty_product(category, sub_category, url)

    html = await fetch_page(page, url)
    if not html:
        logger.error(f"Could not load product page: {url}")
        product["productId"] = extract_model_from_url(url)
        return product

    soup = BeautifulSoup(html, "lxml")

    product["productId"] = _extract_product_id(soup, url)
    product["productName"] = (
        _first_text(soup,
            "h1.product-title", "h1.pdp-header__title", "h1", ".product-name",
            "[data-testid='product-title']", "meta[property='og:title']",
        )
        or _first_attr(soup, "content", "meta[property='og:title']")
    )

    price, mrp = _extract_price(soup)
    product["price"] = price
    product["mrp"] = mrp

    short_desc, full_desc = _extract_descriptions(soup)
    product["shortDescription"] = short_desc
    product["fullDescription"] = full_desc

    product["features"] = _extract_features(soup)
    product["specifications"] = _extract_specifications(soup)
    product["images"] = _extract_images(soup, url)
    product["warranty"] = _extract_warranty(soup)
    product["boxContents"] = _extract_box_contents(soup)
    product["manuals"] = _extract_manuals(soup)
    product["compatibleProducts"] = _extract_compatible_products(soup)

    await random_delay()
    return product
