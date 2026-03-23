#!/usr/bin/env python3
"""Fetch publications from Google Scholar and write to publications.json."""

import json
import time
import sys
from datetime import datetime, timezone

AUTHOR_ID = "9jYlHVgAAAAJ"
OUTPUT_FILE = "publications.json"
MAX_RETRIES = 3


def fetch_with_retry():
    """Fetch author data from Google Scholar with retry logic."""
    from scholarly import scholarly

    # Try using a free proxy to avoid rate limiting
    try:
        from fp.fp import FreeProxy
        proxy = FreeProxy(rand=True, timeout=5).get()
        scholarly.use_proxy(http=proxy, https=proxy)
        print(f"Using proxy: {proxy}")
    except Exception as e:
        print(f"Proxy setup failed, proceeding without proxy: {e}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Attempt {attempt}/{MAX_RETRIES}: Searching for author...")
            author = scholarly.search_author_id(AUTHOR_ID)
            print("Filling author profile...")
            author = scholarly.fill(author, sections=["basics", "indices", "publications"])
            return author
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt * 5
                print(f"Waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                raise


def format_authors(authors_str):
    """Bold any author name containing 'Evans'."""
    if not authors_str:
        return ""
    authors = authors_str.split(", ")
    formatted = []
    for a in authors:
        a = a.strip()
        if "Evans" in a:
            formatted.append(f"<strong>{a}</strong>")
        else:
            formatted.append(a)
    return ", ".join(formatted)


def main():
    from scholarly import scholarly

    print("Fetching publications from Google Scholar...")
    try:
        author = fetch_with_retry()
    except Exception as e:
        print(f"ERROR: All attempts failed: {e}")
        sys.exit(1)

    # Extract profile-level stats
    profile = {
        "citations": author.get("citedby", 0),
        "h_index": author.get("hindex", 0),
        "i10_index": author.get("i10index", 0),
    }
    print(f"Profile stats: {profile}")

    # Extract publications
    publications = []
    for pub in author.get("publications", []):
        try:
            filled = scholarly.fill(pub)
        except Exception:
            filled = pub

        bib = filled.get("bib", {})
        title = bib.get("title", "")
        authors_raw = bib.get("author", "")
        year = bib.get("pub_year", "")
        journal = bib.get("journal", bib.get("venue", bib.get("booktitle", "")))
        volume = bib.get("volume", "")
        number = bib.get("number", "")
        pages = bib.get("pages", "")
        citations = filled.get("num_citations", 0)
        url = filled.get("pub_url", "")

        volume_info = ""
        if volume:
            volume_info = volume
            if number:
                volume_info += f"({number})"
            if pages:
                volume_info += f", {pages}"

        try:
            year_int = int(year)
        except (ValueError, TypeError):
            year_int = 0

        publications.append({
            "title": title,
            "authors": format_authors(authors_raw),
            "year": year_int,
            "journal": journal,
            "volume_info": volume_info,
            "citations": citations,
            "url": url,
        })

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
