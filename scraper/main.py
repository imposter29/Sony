"""
main.py — Orchestrates the full Sony India camera ecosystem scraper.

Usage:
  python main.py           — Full run across all categories
  python main.py --test    — Test run (2 categories only, faster)
  python main.py --headful — Show the browser window while scraping
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

from config import CATEGORIES, OUTPUT_DIR, OUTPUT_FILE
from browser import BrowserSession
from listing_scraper import get_product_urls_for_category
from detail_scraper import scrape_product

# ──────────────────────────────────────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")

# ──────────────────────────────────────────────────────────────────────────────
# Output path
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, OUTPUT_DIR, OUTPUT_FILE))


# ──────────────────────────────────────────────────────────────────────────────
# Main async scrape pipeline
# ──────────────────────────────────────────────────────────────────────────────

async def run(categories: list[dict], headless: bool = True):
    products: list[dict] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()

    async with BrowserSession(headless=headless) as session:
        for cat in categories:
            category = cat["category"]
            sub_cat = cat["subCategory"]
            primary_url = cat["url"]
            fallback_url = cat["fallback_url"]
            label = f"{category}/{sub_cat}" if sub_cat else category

            logger.info(f"\n{'='*60}")
            logger.info(f"CATEGORY: {label}")
            logger.info(f"{'='*60}")

            # ── Step 1: collect product URLs ──────────────────────────────
            product_urls = await get_product_urls_for_category(
                session, primary_url, fallback_url, category, sub_cat,
                filter_selector=cat.get("filter_selector"),
            )

            if not product_urls:
                logger.warning(f"No product URLs found for [{label}]. Skipping.")
                continue

            # ── Step 2: scrape each product ───────────────────────────────
            page = await session.new_page()
            for url in product_urls:
                if url in seen_urls:
                    logger.debug(f"  Skip duplicate URL: {url}")
                    continue
                seen_urls.add(url)

                logger.info(f"  Scraping: {url}")
                try:
                    product = await scrape_product(page, url, category, sub_cat)
                except Exception as exc:
                    logger.error(f"  Error scraping {url}: {exc}")
                    continue

                # Dedup by productId
                pid = product.get("productId")
                if pid and pid in seen_ids:
                    logger.debug(f"  Skip duplicate productId: {pid}")
                    continue
                if pid:
                    seen_ids.add(pid)

                products.append(product)
                logger.info(
                    f"  ✓ [{len(products):04d}] {product.get('productName') or pid or url}"
                )

            await page.close()

    return products


def save_json(products: list[dict], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    logger.info(f"\n✔ Saved {len(products)} products → {path}")


def validate(products: list[dict]) -> bool:
    required = [
        "productId", "productName", "brand", "category", "subCategory",
        "price", "mrp", "currency", "shortDescription", "fullDescription",
        "features", "specifications", "images", "warranty",
        "boxContents", "manuals", "productUrl",
    ]
    errors = []
    seen = set()
    for i, p in enumerate(products):
        for k in required:
            if k not in p:
                errors.append(f"Item {i} missing field: {k}")
        pid = p.get("productId")
        if pid in seen:
            errors.append(f"Duplicate productId: {pid}")
        seen.add(pid)

    if errors:
        logger.error("Validation FAILED:")
        for e in errors:
            logger.error(f"  {e}")
        return False

    logger.info(f"✔ Validation PASSED — {len(products)} products, all fields present, no duplicates")
    return True


# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sony India Camera Ecosystem Scraper")
    parser.add_argument(
        "--test", action="store_true",
        help="Test run: only scrape the first 2 categories"
    )
    parser.add_argument(
        "--headful", action="store_true",
        help="Show the browser window while scraping"
    )
    parser.add_argument(
        "--output", default=OUTPUT_PATH,
        help=f"Output JSON path (default: {OUTPUT_PATH})"
    )
    args = parser.parse_args()

    cats = CATEGORIES[:2] if args.test else CATEGORIES
    out_path = args.output
    if args.test:
        out_path = out_path.replace(".json", "_test.json")

    mode = "TEST" if args.test else "FULL"
    logger.info(f"\n{'#'*60}")
    logger.info(f"Sony India Camera Ecosystem Scraper — {mode} RUN")
    logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Categories: {len(cats)}")
    logger.info(f"Output: {out_path}")
    logger.info(f"{'#'*60}\n")

    products = asyncio.run(run(cats, headless=not args.headful))

    save_json(products, out_path)
    valid = validate(products)

    logger.info(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
