import time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
import re
import json
from datetime import datetime, timezone

BASE_URL = "https://books.toscrape.com/"
FIRST_PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"

CACHE_DIR = Path(__file__).parent.parent / "cache"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

USER_AGENT = "FlyRankInternship-A9/1.0"
REQUEST_DELAY = 0.5

def fetch_page(url, cache_file):
    """
    Fetch a page from the website or read it from local cache.

    Retry once for timeouts and 5xx server errors.
    Do not retry 403 or 404.
    """

    # Cache hit
    if cache_file.exists():

        html = cache_file.read_text(
            encoding="utf-8"
        )

        print(f"CACHE HIT {url}")
        print(f"size={len(html)} bytes")

        return html, True

    print(f"FETCH {url}")

    headers = {
        "User-Agent": USER_AGENT
    }

    for attempt in range(2):

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )

            # Successful request
            if response.status_code == 200:

                html = response.content.decode(
                    "utf-8"
                )

                cache_file.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                cache_file.write_text(
                    html,
                    encoding="utf-8"
                )

                print(
                    f"status={response.status_code}"
                )

                print(
                    f"size={len(html)} bytes"
                )

                return html, False

            # Do NOT retry 403
            if response.status_code == 403:

                raise RuntimeError(
                    f"Fetch failed: {url} returned 403"
                )

            # Do NOT retry 404
            if response.status_code == 404:

                raise RuntimeError(
                    f"Fetch failed: {url} returned 404"
                )

            # Retry 5xx once
            if 500 <= response.status_code <= 599:

                if attempt == 0:

                    print(
                        f"Server error "
                        f"{response.status_code}. "
                        f"Retrying once..."
                    )

                    time.sleep(REQUEST_DELAY)

                    continue

                raise RuntimeError(
                    f"Fetch failed after retry: "
                    f"{url} returned "
                    f"{response.status_code}"
                )

            # Other HTTP errors
            raise RuntimeError(
                f"Fetch failed: "
                f"{url} returned "
                f"{response.status_code}"
            )

        except requests.Timeout:

            if attempt == 0:

                print(
                    "Request timed out. "
                    "Retrying once..."
                )

                time.sleep(REQUEST_DELAY)

                continue

            raise RuntimeError(
                f"Request timed out after retry: {url}"
            )

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

        html, _ = fetch_page(
            current_url,
            cache_file
        )

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        # Find all book links
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

    unique_book_urls = list(
        dict.fromkeys(all_book_urls)
    )

    print()
    print(
        f"catalogue_pages={catalogue_pages}"
    )
    print(
        f"discovered={len(all_book_urls)}"
    )
    print(
        f"unique_urls={len(unique_book_urls)}"
    )

    return unique_book_urls

class Book(BaseModel):
    title: str
    price: float
    availability: int
    rating: int = Field(ge=1, le=5)
    upc: str
    product_type: str
    tax: float
    description: str

def normalize_price(value):

    if value is None:

        raise ValueError(
            "Price was not found on the page"
        )

    match = re.search(
        r"\d+(?:\.\d+)?",
        value
    )

    if not match:
        raise ValueError(
            f"Could not parse price: {value}"
        )

    return float(match.group())

def normalize_availability(value):

    if value is None:
        raise ValueError(
            "Availability was not found on the page"
        )

    start = value.find("(")
    end = value.find(" available)")

    if start == -1 or end == -1:
        raise ValueError(
            f"Could not parse availability: {value}"
        )

    return int(
        value[start + 1:end]
    )

def normalize_rating(value):

    if value is None:
        raise ValueError(
            "Rating was not found on the page"
        )

    ratings = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5,
    }

    if value not in ratings:
        raise ValueError(
            f"Unknown rating: {value}"
        )

    return ratings[value]

def normalize_tax(value):

    if value is None:

        raise ValueError(
            "Tax was not found on the page"
        )

    match = re.search(
        r"\d+(?:\.\d+)?",
        value
    )

    if not match:
        raise ValueError(
            f"Could not parse tax: {value}"
        )

    return float(match.group())

def scrape_book(url, index):
    """
    Visit one book detail page and extract
    the eight raw fields.
    """

    cache_file = (
        CACHE_DIR /
        f"book-{index:03d}.html"
    )

    html, cache_hit = fetch_page(
        url,
        cache_file
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # Title
    title_element = soup.select_one(
        "div.product_main h1"
    )

    title = (
        title_element.get_text(strip=True)
        if title_element
        else None
    )

    # Price
    price_element = soup.select_one(
        "div.product_main .price_color"
    )

    price = (
        price_element.get_text(strip=True)
        if price_element
        else None
    )

    # Availability
    availability_element = soup.select_one(
        "div.product_main .availability"
    )

    availability = (
        availability_element.get_text(
            " ",
            strip=True
        )
        if availability_element
        else None
    )

    # Rating
    rating = None

    rating_element = soup.select_one(
        "div.product_main p.star-rating"
    )

    if rating_element:

        classes = rating_element.get(
            "class",
            []
        )

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

    # Product information table
    product_info = {}

    rows = soup.select(
        "table.table.table-striped tr"
    )

    for row in rows:

        header = row.find("th")
        cell = row.find("td")

        if header and cell:

            key = header.get_text(
                " ",
                strip=True
            )

            value = cell.get_text(
                " ",
                strip=True
            )

            product_info[key] = value

    # UPC
    upc = product_info.get("UPC")

    # Product Type
    product_type = product_info.get(
        "Product Type"
    )

    # Books to Scrape does not provide tax
    tax = "£0.00"

    # Description
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
        "_cache_hit": cache_hit,
    }

def scrape_all_books(book_urls):

    records = []
    errors = []

    pages_fetched = 0
    cache_hits = 0
    failed_pages = 0

    for index, url in enumerate(
        book_urls,
        start=1
    ):

        print()
        print(
            f"BOOK {index}/{len(book_urls)}"
        )
        try:
            raw_record = scrape_book(
                url,
                index
            )
            # Track cache/fetch
            if raw_record["_cache_hit"]:

                cache_hits += 1
            else:
                pages_fetched += 1

            normalized_record = {
                "title": raw_record["title"],
                "price": normalize_price(
                    raw_record["price"]
                ),

                "availability":
                    normalize_availability(
                        raw_record["availability"]
                    ),

                "rating": normalize_rating(
                    raw_record["rating"]
                ),
                "upc": raw_record["upc"],

                "product_type":
                    raw_record["product_type"],

                "tax": normalize_tax(
                    raw_record["tax"]
                ),

                "description":
                    raw_record["description"],
            }

            book = Book(
                **normalized_record
            )

            records.append(book)

            if index == 1:
                print()
                print(
                    "FIRST VALIDATED RECORD"
                )

                print(
                    book.model_dump()
                )

        except Exception as exc:

            print(
                f"ERROR scraping {url}: {exc}"
            )

            failed_pages += 1

            errors.append({
                "url": url,
                "error": str(exc)
            })

        # Delay only before an uncached next request
        if index < len(book_urls):

            next_cache_file = (
                CACHE_DIR /
                f"book-{index + 1:03d}.html"
            )

            if not next_cache_file.exists():

                time.sleep(
                    REQUEST_DELAY
                )

    return (
        records,
        errors,
        pages_fetched,
        cache_hits,
        failed_pages
    )


# --------------------------------------------------
# SAVE JSON
# --------------------------------------------------

def save_json(filename, data):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        OUTPUT_DIR / filename
    )

    with output_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    started_at = datetime.now(
        timezone.utc
    )

    # Discover the normal 60 URLs
    book_urls = discover_books()

    print()

    if len(book_urls) != 60:

        raise RuntimeError(
            f"Expected 60 unique book URLs, "
            f"but found {len(book_urls)}"
        )

    # --------------------------------------------------
    # STAGE 5 FAILURE TEST
    # --------------------------------------------------

    # Add ONE fake URL intentionally.
    book_urls.append(
        "https://books.toscrape.com/"
        "catalogue/fake-book-that-does-not-exist_99999/"
        "index.html"
    )

    print(
        f"URLs to process including test failure: "
        f"{len(book_urls)}"
    )

    # Scrape
    (
        records,
        errors,
        pages_fetched,
        cache_hits,
        failed_pages
    ) = scrape_all_books(
        book_urls
    )

    finished_at = datetime.now(
        timezone.utc
    )

    # Convert Pydantic models
    books_data = [
        book.model_dump()
        for book in records
    ]

    # Save books.json
    save_json(
        "books.json",
        books_data
    )

    # Save errors.json
    save_json(
        "errors.json",
        errors
    )

    # Duration
    duration = (
        finished_at - started_at
    ).total_seconds()

    # Stage 5 run report
    run_report = {

        "started_at":
            started_at.isoformat(),

        "finished_at":
            finished_at.isoformat(),

        "duration_seconds":
            duration,

        "pages_fetched":
            pages_fetched,

        "cache_hits":
            cache_hits,

        "valid_records":
            len(records),

        "invalid_records":
            len(errors),

        "failed_pages":
            failed_pages,
    }

    # Save report
    save_json(
        "run-report.json",
        run_report
    )

    print()

    print(
        f"pages_fetched={pages_fetched}"
    )

    print(
        f"cache_hits={cache_hits}"
    )

    print(
        f"valid_records={len(records)}"
    )

    print(
        f"invalid_records={len(errors)}"
    )

    print(
        f"failed_pages={failed_pages}"
    )

    print()

    print(
        "Output files created:"
    )

    print(
        "  output/books.json"
    )

    print(
        "  output/errors.json"
    )

    print(
        "  output/run-report.json"
    )