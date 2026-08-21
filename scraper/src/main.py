import time
from pathlib import Path

import requests


# The catalogue page we want to download
PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"

# Location where we will save the downloaded HTML
CACHE_FILE = Path(__file__).parent.parent / "cache" / "catalogue-page-1.html"

# Identify our scraper honestly
USER_AGENT = "FlyRankInternship-A9/1.0"


def fetch_page():
    # ---------------------------------------------------------
    # 1. Check whether we already have a cached copy
    # ---------------------------------------------------------
    if CACHE_FILE.exists():
        html = CACHE_FILE.read_text(encoding="utf-8")

        print("CACHE HIT")
        print(f"size={len(html)} bytes")

        return html

    # ---------------------------------------------------------
    # 2. No cache exists, so make a real request
    # ---------------------------------------------------------
    print("FETCH")
    print(PAGE_URL)

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(
            PAGE_URL,
            headers=headers,
            timeout=10
        )

        # -----------------------------------------------------
        # 3. Check the HTTP status code
        # -----------------------------------------------------
        if response.status_code != 200:
            raise RuntimeError(
                f"Fetch failed with status {response.status_code}"
            )

        html = response.text

        # -----------------------------------------------------
        # 4. Save the HTML to our cache
        # -----------------------------------------------------
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        CACHE_FILE.write_text(
            html,
            encoding="utf-8"
        )

        print(f"status={response.status_code}")
        print(f"size={len(html)} bytes")

        return html

    except requests.RequestException as error:
        raise RuntimeError(f"Request failed: {error}")


if __name__ == "__main__":
    fetch_page()