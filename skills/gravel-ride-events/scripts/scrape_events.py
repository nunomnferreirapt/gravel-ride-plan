#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.28", "beautifulsoup4>=4.12"]
# ///
"""Scrape gravel cycling events from public calendars near Amsterdam.

Usage:
    uv run scrape_events.py --start 2026-03-28 --end 2026-03-30

Output: JSON array of events to stdout, progress to stderr.
Dependencies: requests, beautifulsoup4 (resolved by uv from the header above,
or install them yourself and use python3).
"""

import argparse
import json
import re
import sys
from datetime import datetime, date
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# Cities within ~1h drive of Amsterdam
NEARBY_CITIES = {
    "amsterdam", "haarlem", "leiden", "utrecht", "hilversum", "amersfoort",
    "almere", "zaandam", "alkmaar", "hoorn", "purmerend", "bussum",
    "naarden", "weesp", "muiden", "laren", "blaricum", "huizen",
    "gouda", "delft", "den haag", "the hague", "rotterdam", "breda",
    "arnhem", "nijmegen", "apeldoorn", "deventer", "zwolle", "lelystad",
    "veluwe", "het gooi", "gooi", "drenthe", "flevoland", "zeist",
    "soest", "baarn", "loosdrecht", "vinkeveen", "abcoude", "wijk bij duurstede",
    "rhenen", "wageningen", "ede", "barneveld", "harderwijk", "ermelo",
    "nunspeet", "elburg", "hattem", "heerde", "epe", "vaassen",
    "zevenaar", "doetinchem", "winterswijk", "lochem", "zutphen",
    "nord-holland", "north holland", "zuid-holland", "south holland",
    "gelderland", "overijssel", "utrecht province", "flevoland",
    "netherlands", "nederland", "holland",
}


def is_nearby(location: str) -> bool:
    """Check if a location string matches a city within ~1h of Amsterdam."""
    if not location:
        return True
    loc_lower = location.lower()
    return any(city in loc_lower for city in NEARBY_CITIES)


def in_date_range(event_date: Optional[date], start: date, end: date) -> bool:
    """Check if an event date falls within the requested range."""
    if event_date is None:
        return True
    return start <= event_date <= end


def parse_date_flexible(text: str, year: Optional[int] = None) -> Optional[date]:
    """Try multiple date formats to parse a date string."""
    text = text.strip()
    if year is None:
        year = date.today().year
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y",
        "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y",
        "%B %d", "%b %d", "%d %B", "%d %b",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            if dt.year == 1900:
                dt = dt.replace(year=year)
            return dt.date()
        except ValueError:
            continue
    return None


def scrape_battistrada(start: date, end: date) -> list[dict]:
    """Scrape gravel events from Battistrada Netherlands calendar.

    Page structure: each event has two <a> tags sharing the same href:
    1. Date link: <a title="(21 Mar 2026) Event Name"> with .ai1ec-date-title div
    2. Title link: <a class="event-title"> with clean event name
    Location and distance are in a sibling .row div.
    """
    events = []
    seen_urls: set[str] = set()
    base_url = "https://battistrada.com/en/cycling-calendar/netherlands/gravel/"

    for page in range(1, 7):
        params = {"biketype": "4"}
        if page > 1:
            params["pg"] = str(page)

        try:
            resp = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[battistrada] Page {page} fetch error: {e}", file=sys.stderr)
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Use the title links (a.event-title) as the primary selector
        title_links = soup.select("a.event-title")

        if not title_links:
            break

        for title_link in title_links:
            try:
                href = title_link.get("href", "")
                url = urljoin("https://battistrada.com", href)

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                # Event name from title link text or title attribute
                name = title_link.get_text(strip=True)
                if not name:
                    name = title_link.get("title", "").replace(" 2026", "").replace(" 2027", "").strip()
                if not name:
                    continue

                # Extract date from the sibling date link (same href, has .ai1ec-date-title)
                event_date = None
                # Find the date link: look for another <a> with same href and date info
                date_link = soup.find("a", href=href, title=re.compile(r"\(\d{1,2}\s+\w{3}\s+\d{4}\)"))
                if date_link:
                    title_text = date_link.get("title", "")
                    date_match = re.search(r"\((\d{1,2})\s+(\w{3})\s+(\d{4})\)", title_text)
                    if date_match:
                        event_date = parse_date_flexible(
                            f"{date_match.group(1)} {date_match.group(2)}",
                            year=int(date_match.group(3))
                        )

                if not in_date_range(event_date, start, end):
                    continue

                # Find the parent row to extract location, distance, event type
                # Title link is inside: div.row > div.col-sm-9 > span > a.event-title
                parent_row = title_link.find_parent("div", class_="row")
                location = ""
                distance = ""
                event_type = ""

                if parent_row:
                    # Location: text after the country flag image
                    # Structure: <span class="tooltip-custom"><img><span>Country</span></span> City
                    loc_container = parent_row.select_one(".col-sm-7")
                    if loc_container:
                        loc_text = loc_container.get_text(" ", strip=True)
                        # Extract city: it's after the country name
                        tooltip = loc_container.select_one(".tooltip-custom")
                        if tooltip:
                            country = tooltip.get_text(strip=True)
                            # City is the text after the tooltip span
                            remaining = loc_text.replace(country, "", 1).strip()
                            # City is before the bike icon text
                            city_match = re.match(r"^([A-Za-zÀ-ÿ\s'-]+?)(?:\s*(?:gravel|road|mtb|cyclo|fat|race|ride|handbike))", remaining, re.IGNORECASE)
                            if city_match:
                                location = city_match.group(1).strip()
                            elif remaining:
                                # Take first word(s) that look like a city
                                location = remaining.split("gravel")[0].split("road")[0].split("mtb")[0].strip().rstrip(",")

                    # Distance: span.distance elements
                    dist_spans = parent_row.select("span.distance")
                    if dist_spans:
                        distances = [s.get_text(strip=True) for s in dist_spans if s.get_text(strip=True)]
                        if distances:
                            distance = " / ".join(distances) + " km"

                    # Event type: bike types + category after the bicycle icon
                    # e.g., "gravel, road - cyclosportive, ride"
                    if loc_container:
                        type_spans = loc_container.select("span.d-block.d-sm-inline")
                        for ts in type_spans:
                            ts_text = ts.get_text(" ", strip=True)
                            if any(kw in ts_text.lower() for kw in ("gravel", "road", "mtb", "race", "ride")):
                                event_type = ts_text.strip()
                                break
                        else:
                            # Fallback: grab all text after city
                            full_loc_text = loc_container.get_text(" ", strip=True)
                            type_match = re.search(
                                r"(?:gravel|road|mtb|cyclo|fat bike|handbike)[\w\s,\-]*",
                                full_loc_text, re.IGNORECASE
                            )
                            if type_match:
                                event_type = type_match.group(0).strip()

                is_gravel = "gravel" in event_type.lower() if event_type else "gravel" in name.lower()
                gravel_only = is_gravel and not any(
                    kw in event_type.lower() for kw in ("road", "mtb", "cyclo-cross", "fat bike")
                ) if event_type else False

                events.append({
                    "source": "Battistrada",
                    "name": name,
                    "date": event_date.isoformat() if event_date else None,
                    "location": location or "Netherlands",
                    "distance": distance,
                    "url": url,
                    "price": None,
                    "type": event_type,
                    "gravel": is_gravel,
                    "gravel_only": gravel_only,
                })
            except Exception as e:
                print(f"[battistrada] Parse error: {e}", file=sys.stderr)
                continue

    return events


def scrape_maats(start: date, end: date) -> list[dict]:
    """Scrape events from Maats.cc Shopify products JSON API.

    Shopify endpoint: /collections/events/products.json?page=N&limit=50
    Products have title, handle, variants (with price), and tags.
    Dates are in title or variant titles (e.g., "Zwolle - 08/11").
    Recurring community rides (Flow Rides, Advanced Rides, Gravel Rides) have no
    specific date: include them with a note.
    """
    events = []
    page = 1
    # Known recurring ride patterns (no specific date, happen weekly/regularly)
    RECURRING_PATTERNS = ("flow ride", "advanced ride", "gravel ride", "community ride")

    while True:
        url = f"https://maats.cc/collections/events/products.json?page={page}&limit=50"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"[maats] Fetch error page {page}: {e}", file=sys.stderr)
            break

        products = data.get("products", [])
        if not products:
            break

        for product in products:
            try:
                title = product.get("title", "")
                handle = product.get("handle", "")
                title_lower = title.lower()

                # Skip non-event products
                if "membership" in title_lower:
                    continue

                # Check if any variant is available (sold out = past event)
                variants = product.get("variants", [])
                any_available = any(v.get("available", False) for v in variants)
                if not any_available:
                    continue  # Skip sold-out / past events

                # Parse date from title (e.g., "Maats Pizza Ride Utrecht - Thu 19 June")
                event_date = None
                date_match = re.search(
                    r"(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)",
                    title, re.IGNORECASE
                )
                if date_match:
                    event_date = parse_date_flexible(
                        f"{date_match.group(1)} {date_match.group(2)}", year=start.year
                    )

                # Check for year in title/handle to skip old events
                year_match = re.search(r"20(2[0-5])", title + " " + handle)
                if year_match and int("20" + year_match.group(1)) < start.year:
                    continue

                # For multi-variant events with dates in variants
                variant_events = []
                for variant in variants:
                    if not variant.get("available", False):
                        continue
                    variant_title = variant.get("title", "")
                    var_date_match = re.search(r"(\d{2})/(\d{2})", variant_title)
                    if var_date_match:
                        day = int(var_date_match.group(1))
                        month = int(var_date_match.group(2))
                        try:
                            var_date = date(start.year, month, day)
                        except ValueError:
                            var_date = event_date
                        var_location = variant_title.split(" - ")[0].strip() if " - " in variant_title else ""
                        variant_events.append((var_date, var_location, variant.get("price", "0.00")))
                    elif len(variants) > 1 and variant_title not in ("Default Title", ""):
                        variant_events.append((event_date, variant_title, variant.get("price", "0.00")))

                # Extract location from title
                location = ""
                for city in ("Amsterdam", "Utrecht", "Rotterdam", "Haarlem", "Den Haag",
                             "Arnhem", "Zwolle", "Nijmegen", "Maastricht", "Limburg"):
                    if city.lower() in title_lower:
                        location = city
                        break

                # Detect gravel from title, handle, or tags
                tags = [t.lower() for t in product.get("tags", [])]
                is_gravel = ("gravel" in title_lower or "gravel" in handle
                             or "grv" in title_lower or "gravel" in " ".join(tags))

                if variant_events:
                    for var_date, var_location, var_price in variant_events:
                        if not in_date_range(var_date, start, end):
                            continue
                        price = f"€{float(var_price):.0f}" if var_price and float(var_price) > 0 else "Free"
                        events.append({
                            "source": "Maats",
                            "name": f"{title} ({var_location})" if var_location else title,
                            "date": var_date.isoformat() if var_date else None,
                            "location": var_location or location or "Netherlands",
                            "distance": None,
                            "url": f"https://maats.cc/products/{handle}",
                            "price": price,
                            "gravel": is_gravel,
                        })
                else:
                    # Check if it's a recurring ride (include regardless of date)
                    is_recurring = any(p in title_lower for p in RECURRING_PATTERNS)

                    if event_date:
                        if not in_date_range(event_date, start, end):
                            continue
                    elif not is_recurring:
                        continue  # Skip events with no date unless recurring

                    price_val = variants[0].get("price", "0.00") if variants else "0.00"
                    price = f"€{float(price_val):.0f}" if price_val and float(price_val) > 0 else "Free"

                    events.append({
                        "source": "Maats",
                        "name": title,
                        "date": event_date.isoformat() if event_date else "recurring",
                        "location": location or "Netherlands",
                        "distance": None,
                        "url": f"https://maats.cc/products/{handle}",
                        "price": price,
                        "gravel": is_gravel,
                        **({"recurring": True} if is_recurring else {}),
                    })
            except Exception as e:
                print(f"[maats] Parse error: {e}", file=sys.stderr)
                continue

        page += 1
        if page > 10:
            break

    return events


def scrape_rideout(start: date, end: date) -> list[dict]:
    """Scrape events from Ride Out Amsterdam."""
    events = []
    url = "https://rideout.amsterdam/events/"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[rideout] Fetch error: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find event links
    event_links = soup.select("a[href*='/event/']")
    seen_urls: set[str] = set()

    for link in event_links:
        try:
            href = link.get("href", "")
            event_url = urljoin("https://rideout.amsterdam", href)

            if event_url in seen_urls:
                continue
            seen_urls.add(event_url)

            name = link.get_text(strip=True)
            if not name or len(name) < 3:
                continue

            # Try to get date from the page or surrounding context
            event_date = None
            parent = link.find_parent(["article", "div", "li"])
            search_text = parent.get_text() if parent else name
            date_patterns = [
                r"(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4})",
                r"(\d{1,2}\s+\w+\s+\d{4})",
                r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*)",
            ]
            for pattern in date_patterns:
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    cleaned = re.sub(r"(st|nd|rd|th)", "", match.group(1))
                    event_date = parse_date_flexible(cleaned)
                    if event_date:
                        break

            if not in_date_range(event_date, start, end):
                continue

            # Price
            price = None
            price_match = re.search(r"€\s*[\d,.]+", search_text)
            if price_match:
                price = price_match.group(0)

            is_gravel = "gravel" in name.lower() or "gravel" in search_text.lower()

            events.append({
                "source": "Ride Out Amsterdam",
                "name": name,
                "date": event_date.isoformat() if event_date else None,
                "location": "Amsterdam",
                "distance": None,
                "url": event_url,
                "price": price,
                "gravel": is_gravel,
            })
        except Exception as e:
            print(f"[rideout] Parse error: {e}", file=sys.stderr)
            continue

    return events


def main():
    parser = argparse.ArgumentParser(description="Scrape gravel events near Amsterdam")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--all-locations", action="store_true",
                        help="Include events from all NL locations, not just near Amsterdam")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)

    print(f"Scraping gravel events {start} to {end}...", file=sys.stderr)

    all_events = []

    all_events.extend(scrape_battistrada(start, end))
    print(f"  Battistrada: {len(all_events)} events", file=sys.stderr)

    maats_count = len(all_events)
    all_events.extend(scrape_maats(start, end))
    print(f"  Maats: {len(all_events) - maats_count} events", file=sys.stderr)

    rideout_count = len(all_events)
    all_events.extend(scrape_rideout(start, end))
    print(f"  Ride Out: {len(all_events) - rideout_count} events", file=sys.stderr)

    # Filter by proximity to Amsterdam (unless --all-locations)
    if not args.all_locations:
        all_events = [e for e in all_events if is_nearby(e.get("location", ""))]

    # Sort: gravel events first, then by date
    all_events.sort(key=lambda e: (
        0 if e.get("gravel") else 1,
        e.get("date") or "9999-99-99",
    ))

    print(f"Total: {len(all_events)} events", file=sys.stderr)
    print(json.dumps(all_events, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
