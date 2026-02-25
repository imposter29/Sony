"""
browser.py — Playwright browser lifecycle: launch, stealth headers, retry wrapper.
"""

import asyncio
import random
import logging
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config import REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, PAGE_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)

# Stealth user-agent and headers mimicking a real Chrome browser on macOS
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

EXTRA_HEADERS = {
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}


async def random_delay():
    """Sleep for a random duration to respect rate limits."""
    delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    logger.debug(f"Sleeping {delay:.1f}s")
    await asyncio.sleep(delay)


class BrowserSession:
    """Context manager that owns a Playwright browser + context."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        self.context = await self.browser.new_context(
            user_agent=USER_AGENT,
            extra_http_headers=EXTRA_HEADERS,
            viewport={"width": 1440, "height": 900},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        # Hide webdriver flag
        await self.context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return self

    async def __aexit__(self, *args):
        await self.context.close()
        await self.browser.close()
        await self._playwright.stop()

    async def new_page(self) -> Page:
        page = await self.context.new_page()
        page.set_default_timeout(PAGE_TIMEOUT)
        page.set_default_navigation_timeout(PAGE_TIMEOUT)
        return page


async def fetch_page(page: Page, url: str) -> str | None:
    """
    Navigate to a URL with retry logic.
    Returns rendered HTML or None on failure.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded")
            # Extra wait for JS-rendered content
            await page.wait_for_timeout(2500)
            html = await page.content()
            return html
        except Exception as exc:
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed for {url}: {exc}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)   # exponential backoff
    logger.error(f"All retries exhausted for {url}")
    return None


async def scroll_to_load_all(page: Page, pause: float = 1.5):
    """
    Scroll the page incrementally to trigger lazy-load / infinite scroll.
    Stops when the page height stops increasing.
    """
    prev_height = 0
    while True:
        curr_height = await page.evaluate("document.body.scrollHeight")
        if curr_height == prev_height:
            break
        prev_height = curr_height
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(pause)
