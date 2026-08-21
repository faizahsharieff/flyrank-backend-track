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

    try:
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

    except requests.RequestException as error:
        raise RuntimeError(
            f"Request failed for {url}: {error}"
        )


def discover_books():
    """
    Discover all books from the first three catalogue pages.
    """

    current_url = FIRST_PAGE_URL

    all_book_urls = []
    catalogue_pages = 0

    while current_url and catalogue_pages < 3:

        catalogue_pages += 1

        cache_file = (
            CACHE_DIR /
            f"catalogue-page-{catalogue_pages}.html"
        )

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

        # Find the next catalogue page
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

        if current_url and catalogue_pages < 3:
            time.sleep(REQUEST_DELAY)

    # Remove duplicate URLs
    unique_book_urls = list(
        dict.fromkeys(all_book_urls)
    )

    print()
    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(all_book_urls)}")
    print(f"unique_urls={len(unique_book_urls)}")

    return unique_book_urls


def scrape_book(url, index):
    """
    Visit one book detail page and extract the eight raw fields.
    """

    cache_file = CACHE_DIR / f"book-{index:03d}.html"

    html = fetch_page(
        url,
        cache_file
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    title_element = soup.select_one(
        "div.product_main h1"
    )

    title = (
        title_element.get_text(strip=True)
        if title_element
        else None
    )

    price_element = soup.select_one(
        "div.product_main .price_color"
    )

    price = (
        price_element.get_text(strip=True)
        if price_element
        else None
    )

    availability_element = soup.select_one(
        "div.product_main .availability"
    )

    availability = (
        availability_element.get_text(" ", strip=True)
        if availability_element
        else None
    )
    rating = None

    rating_element = soup.select_one(
        "div.product_main p.star-rating"
    )

    if rating_element:

        classes = rating_element.get("class", [])

        rating_classes = {
            "One",
            "Two",
            "Three",
            "Four",
            "Five"
        }

        for class_name in classes:

            if class_name in rating_classes:
                rating = class_name
                break
    product_info = {}

    rows = soup.select(
        "table.table.table-striped tr"
    )

    for row in rows:

        cells = row.find_all("td")

        if len(cells) == 2:

            key = cells[0].get_text(
                " ",
                strip=True
            )

            value = cells[1].get_text(
                " ",
                strip=True
            )

            product_info[key] = value

    # Universal Product Code (UPC)
    upc = product_info.get(
        "UPC"
    )
    product_type = product_info.get(
        "Product Type"
    )
    tax = product_info.get(
        "Tax"
    )
    description_element = soup.select_one(
        "#product_description + p"
    )
    description = (
        description_element.get_text(
            " ",
            strip=True
        )
        if description_element
        else None
    )
    return {
        "title": title,
        "price": price,
        "availability": availability,
        "rating": rating,
        "upc": upc,
        "product_type": product_type,
        "tax": tax,
        "description": description,
    }
def scrape_all_books(book_urls):
    """
    Scrape all 60 individual book pages.
    """

    records = []

    for index, url in enumerate(
        book_urls,
        start=1
    ):

        print()
        print(
            f"BOOK {index}/{len(book_urls)}"
        )
        try:
            record = scrape_book(
                url,
                index
            )
            records.append(
                record
            )
            if index == 1:

                print()
                print("FIRST RAW RECORD")
                print(record)

        except Exception as error:

            print(
                f"ERROR scraping {url}: {error}"
            )
        # Wait before the next real request.
        # Cached pages don't need a delay.
        if index < len(book_urls):

            next_cache_file = (
                CACHE_DIR /
                f"book-{index + 1:03d}.html"
            )

            if not next_cache_file.exists():
                time.sleep(REQUEST_DELAY)

    return records
if __name__ == "__main__":

    book_urls = discover_books()

    print()

    if len(book_urls) != 60:
        raise RuntimeError(
            f"Expected 60 unique book URLs, "
            f"but found {len(book_urls)}"
        )

    records = scrape_all_books(
        book_urls
    )

    print()
    print(
        f"records_scraped={len(records)}"
    )

    cached_books = list(
        CACHE_DIR.glob("book-*.html")
    )

    print(
        f"cached_detail_pages={len(cached_books)}"
    )