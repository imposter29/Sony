"""
config.py — All tunable constants for the Sony India camera ecosystem scraper.
"""

BASE_URL = "https://www.sony.co.in"
OUTPUT_DIR = ".."           # relative to scraper/; output goes to Sony/
OUTPUT_FILE = "sony_camera_ecosystem.json"

# Min/max random delay between page requests (seconds)
REQUEST_DELAY_MIN = 2.0
REQUEST_DELAY_MAX = 4.5

# Max retries per page before giving up
MAX_RETRIES = 3

# Playwright page load timeout (ms)
PAGE_TIMEOUT = 60_000

# ──────────────────────────────────────────────────────────────────────────────
# Category map: (category, subCategory) → listing URL paths
# URLs verified via browser inspection of sony.co.in on 2026-02-21.
# Sony uses /gallery suffix for product grids.
# Lenses use a single gallery page with AJAX filters for sub-categories.
# ──────────────────────────────────────────────────────────────────────────────

CATEGORIES = [
    # ── Interchangeable-Lens Cameras ──────────────────────────────────────────
    {
        "category": "Interchangeable-Lens Cameras",
        "subCategory": "Full Frame Mirrorless",
        "url": f"{BASE_URL}/interchangeable-lens-cameras/full-frame-e-mount-mirrorless",
        "fallback_url": f"{BASE_URL}/interchangeable-lens-cameras/gallery",
    },
    {
        "category": "Interchangeable-Lens Cameras",
        "subCategory": "APS-C Mirrorless",
        "url": f"{BASE_URL}/interchangeable-lens-cameras/aps-c-e-mount-mirrorless",
        "fallback_url": f"{BASE_URL}/interchangeable-lens-cameras/gallery",
    },
    # ── Compact Cameras ───────────────────────────────────────────────────────
    {
        "category": "Compact Cameras",
        "subCategory": None,
        "url": f"{BASE_URL}/compact-cameras/gallery",
        "fallback_url": f"{BASE_URL}/compact-cameras",
    },
    # ── Vlog Cameras ──────────────────────────────────────────────────────────
    {
        "category": "Vlog Cameras",
        "subCategory": None,
        "url": f"{BASE_URL}/vlog-cameras/gallery",
        "fallback_url": f"{BASE_URL}/vlog-cameras",
    },
    # ── Cinema Line Cameras ───────────────────────────────────────────────────
    {
        "category": "Cinema Line Cameras",
        "subCategory": None,
        "url": f"{BASE_URL}/cinema-line/gallery",
        "fallback_url": f"{BASE_URL}/electronics/cinema-line",
    },
    # ── Lenses ────────────────────────────────────────────────────────────────
    # Sony serves all lens sub-categories from one gallery page with JS filters.
    # The scraper visits each filter URL variant.
    {
        "category": "Lenses",
        "subCategory": "Prime",
        "url": f"{BASE_URL}/lenses/gallery?filter=prime-lenses",
        "fallback_url": f"{BASE_URL}/lenses/gallery",
        "filter_selector": "input#facet-lens-type-prime-lenses",
    },
    {
        "category": "Lenses",
        "subCategory": "Zoom",
        "url": f"{BASE_URL}/lenses/gallery?filter=zoom-lenses",
        "fallback_url": f"{BASE_URL}/lenses/gallery",
        "filter_selector": "input#facet-lens-type-zoom-lenses",
    },
    {
        "category": "Lenses",
        "subCategory": "G Master",
        "url": f"{BASE_URL}/lenses/gallery?filter=g-master",
        "fallback_url": f"{BASE_URL}/lenses/gallery",
        "filter_selector": "input#facet-sub-brand-g-master",
    },
    {
        "category": "Lenses",
        "subCategory": "Wide",
        "url": f"{BASE_URL}/lenses/gallery?filter=wide-angle-lenses",
        "fallback_url": f"{BASE_URL}/lenses/gallery",
        "filter_selector": None,
    },
    {
        "category": "Lenses",
        "subCategory": "Telephoto",
        "url": f"{BASE_URL}/lenses/gallery?filter=telephoto-lenses",
        "fallback_url": f"{BASE_URL}/lenses/gallery",
        "filter_selector": None,
    },
    # ── Camera Accessories ────────────────────────────────────────────────────
    {
        "category": "Camera Accessories",
        "subCategory": "Batteries",
        "url": f"{BASE_URL}/camera-accessories/batteries/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Chargers",
        "url": f"{BASE_URL}/camera-accessories/chargers/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Vertical Grips",
        "url": f"{BASE_URL}/camera-accessories/vertical-grips/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Microphones",
        "url": f"{BASE_URL}/camera-accessories/microphones/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Flashes",
        "url": f"{BASE_URL}/camera-accessories/flashes/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Tripods",
        "url": f"{BASE_URL}/camera-accessories/tripods/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Shooting Grips",
        "url": f"{BASE_URL}/camera-accessories/shooting-grips/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Straps",
        "url": f"{BASE_URL}/camera-accessories/straps/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Cases",
        "url": f"{BASE_URL}/camera-accessories/cases-and-bags/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Memory Cards",
        "url": f"{BASE_URL}/memory-cards/gallery",
        "fallback_url": f"{BASE_URL}/memory-cards",
    },
    {
        "category": "Camera Accessories",
        "subCategory": "Remote Controls",
        "url": f"{BASE_URL}/camera-accessories/remote-controls/gallery",
        "fallback_url": f"{BASE_URL}/camera-accessories/gallery",
    },
]
