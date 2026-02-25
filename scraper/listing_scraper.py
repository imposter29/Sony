"""
listing_scraper.py — Collects all product URLs from a category listing page.
Handles Sony India's gallery-format pages with ProductTileGallery containers.
"""

import logging
import json
from bs4 import BeautifulSoup

from browser import BrowserSession, fetch_page, scroll_to_load_all, random_delay
from utils import normalize_url

logger = logging.getLogger(__name__)

BASE = "https://www.sony.co.in"

# ──────────────────────────────────────────────────────────────────────────────
# Sony India uses .ProductTileGallery_Container cards with "Learn More" links.
# Priority order: most-specific → most-generic.
# ──────────────────────────────────────────────────────────────────────────────
PRODUCT_LINK_SELECTORS = [
    # Sony India gallery pages — "Learn More" buttons on product cards
    "a.generic-button.primary",
    # Product tile containers holding a link
    ".ProductTileGallery_Container a",
    # Legacy / alternate page types
    "a.product-tile__link",
    "a.product-card__link",
    ".product-list-item a",
    ".product-grid a",
    # Any anchor whose href contains Sony product path patterns
    "a[href*='/interchangeable-lens-cameras/products/']",
    "a[href*='/compact-cameras/products/']",
    "a[href*='/vlog-cameras/products/']",
    "a[href*='/cinema-line/products/']",
    "a[href*='/lenses/products/']",
    "a[href*='/camera-accessories/products/']",
    "a[href*='/memory-cards/products/']",
    "a[href*='/p/ILCE']",
    "a[href*='/p/SEL']",
    "a[href*='/p/DSC']",
    "a[href*='/p/ZV']",
    "a[href*='/p/FX']",
    "a[href*='/p/NP']",
    "a[href*='/p/BC']",
    "a[href*='/p/FA']",
    "a[href*='/p/SF']",
]

LOAD_MORE_SELECTORS = [
    "button.load-more",
    "button[data-component='LoadMore']",
    ".load-more-btn",
    "a.load-more",
]

# Playwright text-based locators for "Load More" / "Show More"
LOAD_MORE_TEXT = ["Load More", "Show More", "View More", "See More", "Load more"]


def _is_product_url(url: str) -> bool:
    """Filter out nav links, assets, and other non-product URLs."""
    lower = url.lower()
    skip_patterns = [
        "/support", "/service", "/about", "/news", "/sitemap",
        "/my-account", "/wishlist", "/cart", "/checkout", "/search",
        "/permalink/",          # known to return 403 Access Denied
        ".jpg", ".png", ".webp", ".svg", ".pdf", ".zip", ".mp4",
        "javascript:", "mailto:", "#",
    ]
    return BASE in url and not any(p in lower for p in skip_patterns)


def _canonical_url(url: str) -> str:
    """Strip query strings and /buy suffixes to get the canonical product URL."""
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    # Remove /buy or /buy/ suffix — these just redirect to the main page
    if path.endswith("/buy"):
        path = path[:-4]
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def _extract_product_urls_from_html(html: str) -> set[str]:
    """Parse rendered HTML and extract all product page URLs."""
    soup = BeautifulSoup(html, "lxml")
    urls: set[str] = set()

    for selector in PRODUCT_LINK_SELECTORS:
        for tag in soup.select(selector):
            href = tag.get("href")
            full = normalize_url(href)
            if full and _is_product_url(full):
                urls.add(_canonical_url(full))

    # Also try JSON-LD structured data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    u = item.get("url") or item.get("@id")
                    if u and _is_product_url(str(u)):
                        urls.add(_canonical_url(str(u)))
        except Exception:
            pass

    return urls


async def _click_load_more(page) -> bool:
    """Try to click a Load More button. Returns True if clicked."""
    for selector in LOAD_MORE_SELECTORS:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible():
                await btn.scroll_into_view_if_needed()
                await btn.click()
                await page.wait_for_timeout(2000)
                return True
        except Exception:
            continue

    # Try text-based locators
    for text in LOAD_MORE_TEXT:
        try:
            btn = page.get_by_role("button", name=text).first
            if await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(2000)
                return True
        except Exception:
            continue

    return False


async def _apply_filter(page, filter_selector: str | None) -> bool:
    """Click a facet/filter checkbox if specified. Returns True on success."""
    if not filter_selector:
        return False
    try:
        cb = page.locator(filter_selector).first
        if await cb.is_visible():
            await cb.click()
            await page.wait_for_timeout(2500)
            return True
    except Exception:
        pass
    return False


async def get_product_urls_for_category(
    session: BrowserSession,
    primary_url: str,
    fallback_url: str,
    category: str,
    sub_category: str | None,
    filter_selector: str | None = None,
) -> list[str]:
    """
    Return a deduplicated list of product page URLs for one category.
    Tries primary_url first; falls back to fallback_url on failure.
    """
    page = await session.new_page()
    collected: set[str] = set()

    for attempt_url in [primary_url, fallback_url]:
        logger.info(f"  → Listing: {attempt_url}")
        html = await fetch_page(page, attempt_url)
        if not html:
            logger.warning(f"    Failed to load {attempt_url}, trying fallback…")
            continue

        # Apply facet filter if this is a filter-based sub-category (e.g. Lenses)
        if filter_selector:
            applied = await _apply_filter(page, filter_selector)
            if applied:
                logger.info(f"    Filter applied: {filter_selector}")
            else:
                logger.warning(f"    Filter NOT applied: {filter_selector}")

        # Scroll to trigger lazy-loaded product cards
        await scroll_to_load_all(page, pause=1.5)

        # Repeatedly click "Load More" until no button is found
        for _ in range(50):   # safety cap
            html = await page.content()
            batch = _extract_product_urls_from_html(html)
            collected.update(batch)
            clicked = await _click_load_more(page)
            if not clicked:
                break
            await page.wait_for_timeout(2000)
            await scroll_to_load_all(page, pause=1.0)

        # Final scrape
        html = await page.content()
        collected.update(_extract_product_urls_from_html(html))

        if collected:
            break   # success — no need to try fallback

        logger.warning(f"    No products found at {attempt_url}")

    await page.close()
    await random_delay()

    urls = sorted(collected)
    label = f"{category}/{sub_category}" if sub_category else category
    logger.info(f"  ✓ {len(urls)} product URLs found for [{label}]")
    return urls
