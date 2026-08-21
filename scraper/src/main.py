import time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
FIRST_PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_DIR = Path(__file__).parent.parent / "cache"

USER_AGENT = "FlyRankInternship-A9/1.0"

REQUEST_DELAY = 0.5

def fetch_page(url, cache_file):
    """
    Fetch a page from the website or read it from the local cache.
    """

    if cache_file.exists():
        html = cache_file.read_text(encoding="utf-8")

        print(f"CACHE HIT {url}")
        print(f"size={len(html)} bytes")

        return html

    print(f"FETCH {url}")

    headers = {
        "User-Agent": USER_AGENT
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed: {url} returned {response.status_code}"
        )

    html = response.text

    cache_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cache_file.write_text(
        html,
        encoding="utf-8"
    )

    print(f"status={response.status_code}")
    print(f"size={len(html)} bytes")

    return html


def discover_books():
    """
    Discover all books from the first three catalogue pages.
    """

    current_url = FIRST_PAGE_URL

    all_book_urls = []
    catalogue_pages = 0

    while current_url and catalogue_pages < 3:

        catalogue_pages += 1

        # Create a cache filename based on the catalogue page number
        cache_file = CACHE_DIR / f"catalogue-page-{catalogue_pages}.html"

        html = fetch_page(
            current_url,
            cache_file
        )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # Find all book links on this catalogue page

        book_links = soup.select(
            "article.product_pod h3 a"
        )

        for link in book_links:

            href = link.get("href")

            if href:
                absolute_url = urljoin(
                    current_url,
                    href
                )

                all_book_urls.append(
                    absolute_url
                )

        # Find the catalogue's "next" link

        next_link = soup.select_one(
            "li.next a"
        )

        if next_link:
            next_href = next_link.get("href")

            current_url = urljoin(
                current_url,
                next_href
            )

        else:
            current_url = None

        # Wait before the next real request

        if current_url and catalogue_pages < 3:
            time.sleep(REQUEST_DELAY)

        # Remove duplicates while preserving order
        
    unique_book_urls = list(
        dict.fromkeys(all_book_urls)
    )

    print()
    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(all_book_urls)}")
    print(f"unique_urls={len(unique_book_urls)}")

    return unique_book_urls

if __name__ == "__main__":
    discover_books()