# Week 5 Assignment: The Polite Scraper

*FlyRank Backend AI Engineering Internship - Web Scraping.*

A Python web scraper built with Requests and BeautifulSoup to collect structured book data from Books to Scrape.

## Overview

The scraper discovers books from the first three catalogue pages of Books to Scrape and extracts information from each book's detail page.

The scraper collects:

- Title
- Price
- Availability
- Rating
- UPC
- Product Type
- Tax
- Description

The extracted data is validated using Pydantic and saved as JSON files.

---

### Technologies used include 
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white) 
![Requests](https://img.shields.io/badge/Requests-HTTP%20Requests-blue) 
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-HTML%20Parsing-green) 
![Pydantic](https://img.shields.io/badge/Pydantic-Validation-red) 
![JSON](https://img.shields.io/badge/JSON-Data%20Storage-lightgrey) 
![pathlib](https://img.shields.io/badge/pathlib-File%20Paths-orange)

## Project Structure

```text
scraper/
├── src/
│   └── main.py
├── cache/
├── output/
│   ├── books.json
│   ├── errors.json
│   └── run-report.json
└── README.md
```
---

# Requirements

- Python 3.10 or later.

## Install the required packages:

```bash
pip install requests beautifulsoup4 pydantic
```

# Running the Scraper

From the project root, run:

```bash
python scraper/src/main.py
```

## The scraper will:
- Discover books from the first three catalogue pages.
- Collect 60 unique book URLs.
- Visit each book detail page.
- Extract and normalize the required fields.
- Validate each record using Pydantic.
- Cache downloaded pages locally.
- Handle individual page failures without stopping the entire run.
- Save the scraped data and run report as JSON.

# Caching

Downloaded catalogue and book pages are stored in the `cache/` directory.

If a page already exists in the cache, the scraper uses the cached copy instead of making another request. This reduces unnecessary requests and makes repeated runs faster.

# Failure Handling

Each book is processed independently. If one page fails, the error is recorded in `errors.json` and the scraper continues processing the remaining pages.

The scraper retries a request once when:
- A request times out,
- The server returns a 5xx error.

The scraper does not retry:
- 403 Forbidden,
- 404 Not Found.

This ensures that one bad page does not terminate the entire scraping run.

# Validation

the following fields are normalized into required types:
| Field | Conversion |
|------|----------|
| price | float |
| availability | integer |
| rating | integer |
| tax | float |

Details about website ratings such as One, Two, Three, Four, and Five are converted into integers from 1 to 5.

# Output Files 
After a run, three files are created in `output/` directory:

`books.json` - Contains all successfully scraped and validated book records.

`errors.json` - Contains information about pages that failed during the run. 
If there are no failures, it contains: 
```json
[]
```
`runs-report.json` - Contains a summary of the scraping run including start time, finish time, duration, pages fetched, cache hits, valid records, invalid records, failed pages.
 
## Stage 5 Failure Test
The scraper includes one intentionally made-up book URL during failure-handling test. The fake page fails without stopping but still saves valid records successfully. 

Expected results: 

```text
valid_records=60; 
failed_pages=1;
```
---

## Actual output received from `run-report.json`
```json
{
  "started_at": "2026-08-26T12:34:21.838438+00:00",
  "finished_at": "2026-08-26T12:34:28.616489+00:00",
  "duration_seconds": 6.778051,
  "pages_fetched": 0,
  "cache_hits": 60,
  "valid_records": 60,
  "invalid_records": 1,
  "failed_pages": 1
}
```

## Ethics Note

This scraper follows responsible scraping practices. When an official API is available, it should be preferred over scraping. The scraper does not bypass logins, paywalls, access restrictions, or blocks, and it collects only the information necessary for the assignment.

## Limitation

The scraper currently processes only the first three catalogue pages, so it collects 60 books instead of covering the entire Books to Scrape catalogue.

Details about source: [Books to Scrape](https://books.toscrape.com/)