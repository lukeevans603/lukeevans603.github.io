#!/usr/bin/env python3
"""Fetch publications from Google Scholar via SerpAPI and write to publications.json."""

import json
import os
import sys
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import urlencode

AUTHOR_ID = "9jYlHVgAAAAJ"
OUTPUT_FILE = "publications.json"
SERPAPI_BASE = "https://serpapi.com/search.json"


def serpapi_request(params):
    """Make a request to SerpAPI and return parsed JSON."""
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("ERROR: SERPAPI_KEY environment variable not set.")
        sys.exit(1)

    params["api_key"] = api_key
    params["engine"] = "google_scholar_author"
    url = f"{SERPAPI_BASE}?{urlencode(params)}"

    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def format_authors(authors_raw):
    """Bold any author name containing 'Evans'."""
    if not authors_raw:
        return ""
    if isinstance(authors_raw, str):
        authors_list = [a.strip() for a in authors_raw.split(",")]
    else:
        authors_list = authors_raw

    formatted = []
    for a in authors_list:
        a = a.strip()
        if "Evans" in a:
            formatted.append(f"<strong>{a}</strong>")
        else:
            formatted.append(a)
    return ", ".join(formatted)


def main():
    print("Fetching publications from Google Scholar via SerpAPI...")

    # First request gives profile info + first batch of articles
    data = serpapi_request({
        "author_id": AUTHOR_ID,
        "start": "0",
        "num": "100",
        "sort": "pubdate",
    })

    # Extract profile stats from cited_by table
    cited_by = data.get("cited_by", {})
    table = cited_by.get("table", [])

    citations_all = 0
    h_index = 0
    i10_index = 0
    for row in table:
        if "citations" in row:
            citations_all = row["citations"].get("all", 0)
        if "h_index" in row:
            h_index = row["h_index"].get("all", 0)
        if "i10_index" in row:
            i10_index = row["i10_index"].get("all", 0)

    profile = {
        "citations": citations_all,
        "h_index": h_index,
        "i10_index": i10_index,
    }
    print(f"Profile stats: {profile}")

    # Collect all articles (paginate if more than 100)
    all_articles = data.get("articles", [])
    print(f"First page: {len(all_articles)} articles")

    start = 100
    while len(all_articles) >= start:
        print(f"Fetching more articles starting at {start}...")
        more_data = serpapi_request({
            "author_id": AUTHOR_ID,
            "start": str(start),
            "num": "100",
            "sort": "pubdate",
        })
        batch = more_data.get("articles", [])
        if not batch:
            break
        all_articles.extend(batch)
        print(f"  Got {len(batch)} more (total: {len(all_articles)})")
        start += 100

    # Process publications
    publications = []
    for article in all_articles:
        title = article.get("title", "")
        authors_raw = article.get("authors", "")
        year_str = article.get("year", "")
        citations = article.get("cited_by", {}).get("value", 0)
        link = article.get("link", "")
        journal = article.get("publication", "")

        try:
            year_int = int(year_str) if year_str else 0
        except (ValueError, TypeError):
            year_int = 0

        publications.append({
            "title": title,
            "authors": format_authors(authors_raw),
            "year": year_int,
            "journal": journal,
            "volume_info": "",
            "citations": citations,
            "url": link,
        })

    # Sort by year descending, then by citations descending
    publications.sort(key=lambda p: (-p["year"], -p["citations"]))

    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "publications": publications,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(publications)} publications to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
