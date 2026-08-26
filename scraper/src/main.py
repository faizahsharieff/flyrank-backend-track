import time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
import re


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
        html = response.content.decode("utf-8")
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
    """
    Convert a price such as '£45.22' into 45.22.
    """

    if value is None:
        raise ValueError("Price was not found on the page")

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

    return int(value[start + 1:end])

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
    """
    Convert a tax value such as '£0.00' into 0.0.
    """

    if value is None:
        raise ValueError("Tax was not found on the page")

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


    upc = product_info.get("UPC")

    product_type = product_info.get("Product Type")

    # Books to Scrape does not provide a Tax row
    tax = "£0.00"
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
            raw_record = scrape_book(
                url,
                index
            )

            normalized_record = {
                "title": raw_record["title"],
                "price": normalize_price(
                    raw_record["price"]
                ),
                "availability": normalize_availability(
                    raw_record["availability"]
                ),
                "rating": normalize_rating(
                    raw_record["rating"]
                ),
                "upc": raw_record["upc"],
                "product_type": raw_record["product_type"],
                "tax": normalize_tax(
                    raw_record["tax"]
                ),
                "description": raw_record["description"],
            }

            book = Book(
                **normalized_record
            )

            records.append(book)

            if index == 1:
                print()
                print("FIRST VALIDATED RECORD")
                print(book.model_dump())

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