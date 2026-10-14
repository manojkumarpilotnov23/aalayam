import json
import re
import uuid
import os
import time
import random
import requests
import cloudscraper

from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse


# ==================================================
# 1. CONFIGURATION
# ==================================================

URLS_FILE = "temple_urls.txt"  # Add one Shaivam temple URL per line


OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_data", "tamil_content.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Reuse a cloudscraper session — it solves Cloudflare JS challenges automatically
# and preserves cookies across requests (same API as requests.Session).
SESSION = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "darwin",
        "desktop": True,
    }
)
SESSION.headers.update(HEADERS)

# Optional: configure GOOGLE_MAPS_API_KEY as an
# environment variable to enable Google Geocoding.
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Coordinates are left null when the page/API does not provide them.
# This avoids assigning one temple's coordinates to every temple.

# ==================================================
# 2. HELPER FUNCTIONS
# ==================================================

def clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def absolute_url(value, base_url):
    if not isinstance(value, str) or not value.strip():
        return None

    result = urljoin(base_url, value.strip())

    if urlparse(result).scheme in ("http", "https"):
        return result

    return None


def get_meta(soup, *names):
    wanted = {name.lower() for name in names}

    for tag in soup.find_all("meta"):
        keys = [
            tag.get("name", ""),
            tag.get("property", ""),
            tag.get("itemprop", "")
        ]

        if any(key.lower() in wanted for key in keys):
            value = clean(tag.get("content"))

            if value:
                return value

    return ""


def walk_objects(value):
    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from walk_objects(child)

    elif isinstance(value, list):
        for child in value:
            yield from walk_objects(child)


def unique_strings(values):
    result = []

    for value in values:
        value = clean(value)

        if value and value not in result:
            result.append(value)

    return result


def valid_coordinates(latitude, longitude):
    try:
        latitude = float(latitude)
        longitude = float(longitude)

        if (
            -90 <= latitude <= 90
            and -180 <= longitude <= 180
        ):
            return latitude, longitude

    except (TypeError, ValueError):
        pass

    return None, None


# ==================================================
# 3. GOOGLE MAPS COORDINATE LOOKUP
# ==================================================

def get_google_coordinates(address):
    """
    Look up coordinates through Google Geocoding API.
    Requires GOOGLE_MAPS_API_KEY to be configured.
    Returns (latitude, longitude), or (None, None).
    """

    if not GOOGLE_MAPS_API_KEY:
        return None, None

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": address,
                "key": GOOGLE_MAPS_API_KEY
            },
            timeout=20
        )

        response.raise_for_status()
        result = response.json()

        if result.get("status") == "OK" and result.get("results"):
            location = (
                result["results"][0]["geometry"]["location"]
            )

            return valid_coordinates(
                location.get("lat"),
                location.get("lng")
            )

        print(
            "Google Geocoding status:",
            result.get("status"),
            result.get("error_message", "")
        )

    except requests.RequestException as error:
        print("Google Maps lookup failed:", error)

    return None, None


# ==================================================
# 3A. GOOGLE PLACES: NEARBY TEMPLES AND HOURS
# ==================================================

# Requires the Google Places API (Legacy) to be enabled for the
# same Google Cloud project as the API key. Results/hours may be
# unavailable for some temples; missing hours are left as null.
NEARBY_TEMPLE_RADIUS_METERS = int(
    os.getenv("NEARBY_TEMPLE_RADIUS_METERS", "10000")
)
MAX_NEARBY_TEMPLES = int(os.getenv("MAX_NEARBY_TEMPLES", "10"))


def get_nearby_temples(latitude, longitude, current_temple_name=""):
    """Return nearby temples and published opening-hour details."""
    if not GOOGLE_MAPS_API_KEY or latitude is None or longitude is None:
        return []

    nearby_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"

    try:
        response = requests.get(
            nearby_url,
            params={
                "location": f"{latitude},{longitude}",
                "radius": NEARBY_TEMPLE_RADIUS_METERS,
                "keyword": "Hindu temple",
                "key": GOOGLE_MAPS_API_KEY,
            },
            timeout=25,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("status") not in ("OK", "ZERO_RESULTS"):
            print("Google Places nearby search status:",
                  result.get("status"), result.get("error_message", ""))
            return []

        temples = []
        current_name = clean(current_temple_name).lower()

        for place in result.get("results", []):
            name = clean(place.get("name"))
            # Do not include the configured/current Natarajar Temple itself.
            if current_name and name.lower() == current_name:
                continue
            if "nataraja" in name.lower() or "natarajar" in name.lower():
                continue

            place_id = place.get("place_id")
            details = {}

            if place_id:
                try:
                    detail_response = requests.get(
                        details_url,
                        params={
                            "place_id": place_id,
                            "fields": (
                                "name,formatted_address,geometry,opening_hours,"
                                "url,website,business_status"
                            ),
                            "key": GOOGLE_MAPS_API_KEY,
                        },
                        timeout=20,
                    )
                    detail_response.raise_for_status()
                    detail_result = detail_response.json()
                    if detail_result.get("status") == "OK":
                        details = detail_result.get("result", {})
                except requests.RequestException as error:
                    print(f"Could not fetch details for {name}: {error}")

            opening = details.get("opening_hours") or place.get("opening_hours") or {}
            location = (details.get("geometry") or place.get("geometry") or {}).get(
                "location", {}
            )

            temples.append({
                "name": details.get("name") or name,
                "address": (
                    details.get("formatted_address")
                    or place.get("vicinity")
                    or ""
                ),
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
                "placeId": place_id,
                "openingHours": opening.get("weekday_text", []),
                "openNow": opening.get("open_now"),
                "businessStatus": details.get("business_status")
                    or place.get("business_status"),
                "googleMapsUrl": details.get("url") or (
                    f"https://www.google.com/maps/search/?api=1&query_place_id={place_id}"
                    if place_id else None
                ),
                "website": details.get("website"),
                "hoursSource": "Google Places" if opening else None,
            })

            if len(temples) >= MAX_NEARBY_TEMPLES:
                break

        return temples

    except requests.RequestException as error:
        print("Google Places nearby temple lookup failed:", error)
        return []



def scrape_temple(input_url):
    """Scrape one temple page and return one JSON-ready dictionary."""
    slug = urlparse(input_url).path.rstrip("/").split("/")[-1] or "temple"
    temple_id = "shaivam-" + re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    print(f"\nProcessing: {input_url}")
    # ==================================================
    # 4. DOWNLOAD WEBSITE
    # ==================================================

    try:
        # Send a Referer that matches the site's own navigation pattern.
        parsed_input = urlparse(input_url)
        referer = f"{parsed_input.scheme}://{parsed_input.netloc}/"
        response = SESSION.get(
            input_url,
            headers={"Referer": referer},
            timeout=40
        )
        if response.status_code == 403:
            # Wait briefly and retry once — some CDNs issue a challenge cookie.
            time.sleep(random.uniform(3, 6))
            response = SESSION.get(
                input_url,
                headers={"Referer": referer},
                timeout=40
            )
        response.raise_for_status()

    except requests.RequestException as error:
        print(f"  ERROR downloading {input_url}: {error}")
        return None

    response.encoding = response.apparent_encoding
    page_url = response.url

    soup = BeautifulSoup(response.text, "html.parser")


    # ==================================================
    # 5. READ STRUCTURED DATA (JSON-LD)
    # ==================================================

    structured_data = []

    for script in soup.find_all(
        "script", type="application/ld+json"
    ):
        try:
            structured_data.append(
                json.loads(script.string or script.get_text())
            )
        except (json.JSONDecodeError, TypeError):
            continue

    objects = [
        obj
        for root in structured_data
        for obj in walk_objects(root)
    ]


    # ==================================================
    # 6. TITLE AND SHORT DESCRIPTION
    # ==================================================

    title = (
        get_meta(soup, "og:title", "twitter:title")
        or (
            soup.title.get_text(" ", strip=True)
            if soup.title else ""
        )
    )

    short_description = get_meta(
        soup,
        "description",
        "og:description",
        "twitter:description"
    )

    if not short_description:
        for obj in objects:
            description = obj.get("description")

            if isinstance(description, str) and description.strip():
                short_description = clean(description)
                break


    # ==================================================
    # 7. CATEGORIES AND TAGS
    # ==================================================

    categories = []
    tags = []

    category_value = get_meta(
        soup, "article:section", "category"
    )

    keywords_value = get_meta(
        soup, "keywords", "news_keywords"
    )

    if category_value:
        categories.extend(
            re.split(r"[,;|]", category_value)
        )

    if keywords_value:
        tags.extend(
            re.split(r"[,;|]", keywords_value)
        )

    for obj in objects:
        section = obj.get("articleSection")

        if isinstance(section, str):
            categories.append(section)

        elif isinstance(section, list):
            categories.extend(section)

        keywords = obj.get("keywords", [])

        if isinstance(keywords, str):
            tags.extend(re.split(r"[,;|]", keywords))

        elif isinstance(keywords, list):
            tags.extend(keywords)

    categories = unique_strings(categories)
    tags = unique_strings(tags)

    # Add only the verified subject category if metadata is absent.
    if not categories:
        categories = ["Hindu Temple", "Shaivism"]

    if not tags:
        tags = [clean(title), "Shaivism"] if title else ["Shaivism"]


    # ==================================================
    # 8. EXTRACT LINKS
    # ==================================================

    links = []
    seen_links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if href.lower().startswith(
            ("javascript:", "mailto:", "tel:")
        ):
            continue

        link_url = absolute_url(href, page_url)

        if not link_url:
            continue

        item = {
            "text": clean(a.get_text(" ", strip=True)),
            "url": link_url
        }

        key = (item["text"], item["url"])

        if key not in seen_links:
            seen_links.add(key)
            links.append(item)


    # ==================================================
    # 9. EXTRACT IMAGES
    # ==================================================

    images = []
    seen_images = set()

    for img in soup.find_all("img"):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-lazy-src")
            or img.get("data-original")
            or img.get("data-url")
        )

        if not src:
            srcset = img.get("srcset") or img.get("data-srcset")

            if srcset:
                src = srcset.split(",")[0].strip().split()[0]

        image_url = absolute_url(src, page_url)

        if not image_url or image_url in seen_images:
            continue

        seen_images.add(image_url)

        images.append({
            "alt": clean(img.get("alt")),
            "title": clean(img.get("title")),
            "url": image_url
        })


    # ==================================================
    # 10. EXTRACT ADDRESS AND COORDINATES
    # ==================================================

    latitude = None
    longitude = None

    city = None
    district = None
    state = None
    country = "India"

    maps_provider = None
    maps_url = None

    for obj in objects:
        obj_type = obj.get("@type", [])

        if isinstance(obj_type, str):
            obj_type = [obj_type]

        is_place = any(
            name in {
                "Place",
                "TouristAttraction",
                "HinduTemple",
                "LandmarksOrHistoricalBuildings",
                "LocalBusiness"
            }
            for name in obj_type
        )

        if not is_place:
            continue

        geo = obj.get("geo") or {}

        if isinstance(geo, dict):
            if latitude is None:
                latitude = geo.get("latitude")

            if longitude is None:
                longitude = geo.get("longitude")

        address = obj.get("address") or {}

        if isinstance(address, dict):
            city = city or address.get("addressLocality")
            state = state or address.get("addressRegion")

            # Do not assume a region is a district.
            district = district or address.get("district")

            address_country = address.get("addressCountry")

            if isinstance(address_country, dict):
                address_country = address_country.get("name")

            country = address_country or country

        # Recognize a Maps URL explicitly supplied in structured data.
        map_value = obj.get("hasMap")

        if isinstance(map_value, str):
            maps_url = absolute_url(map_value, page_url)

        elif isinstance(map_value, dict):
            maps_url = absolute_url(
                map_value.get("url"),
                page_url
            )

        if maps_url:
            maps_provider = "Google Maps" if "google." in maps_url else "Other"


    # Look for coordinate-bearing Google Maps links.
    for a in soup.find_all("a", href=True):
        href = absolute_url(a["href"], page_url)

        if not href:
            continue

        parsed = urlparse(href)

        if "google." not in parsed.netloc.lower():
            continue

        if "maps" not in href.lower():
            continue

        maps_url = maps_url or href
        maps_provider = maps_provider or "Google Maps"

        match = re.search(
            r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)",
            href
        )

        if not match:
            match = re.search(
                r"[?&](?:q|query)=(-?\d+(?:\.\d+)?),"
                r"(-?\d+(?:\.\d+)?)",
                href
            )

        if match:
            latitude = latitude or float(match.group(1))
            longitude = longitude or float(match.group(2))

        if latitude is not None and longitude is not None:
            break


    # Normalize coordinates and reject invalid values.
    latitude, longitude = valid_coordinates(
        latitude, longitude
    )


    # Use a Google Maps lookup if page coordinates are missing.
    # This requires a configured Google Maps API key.
    if latitude is None or longitude is None:
        # Try the page title as a lookup hint; results depend on the API and title quality.
        lookup_address = f"{title}, Tamil Nadu, India" if title else "Tamil Nadu, India"

        api_lat, api_lng = get_google_coordinates(
            lookup_address
        )

        if api_lat is not None and api_lng is not None:
            latitude, longitude = api_lat, api_lng


    if latitude is not None and longitude is not None:
        maps_url = (
            "https://www.google.com/maps/search/?api=1"
            f"&query={latitude},{longitude}"
        )
        maps_provider = "Google Maps"


    # Normalize country and address values.
    for key, value in [
        ("city", city),
        ("district", district),
        ("state", state)
    ]:
        if value:
            if key == "city" and "சிதம்பரம்" in value:
                city = "சிதம்பரம்"
            elif key == "district" and "கடலூர்" in value:
                district = "கடலூர்"
            elif key == "state" and (
                "தமிழ்நாடு" in value or "Tamil Nadu" in value
            ):
                state = "தமிழ்நாடு"

    # Keep missing location fields empty rather than guessing a location.
    city = city or None
    district = district or None
    state = state or None


    # ==================================================
    # 11. EXTRACT TIMINGS
    # ==================================================

    timings = []

    for obj in objects:
        obj_type = obj.get("@type", [])

        if isinstance(obj_type, str):
            obj_type = [obj_type]

        if "OpeningHoursSpecification" in obj_type:
            timings.append({
                "days": obj.get("dayOfWeek", []),
                "opens": obj.get("opens"),
                "closes": obj.get("closes")
            })

    # Do not invent opening hours if they aren't published.
    # Site-specific selectors can be added for a timings table.


    # ==================================================
    # 12. EXTRACT NEARBY TEMPLES
    # ==================================================

    nearby_temples = get_nearby_temples(
        latitude,
        longitude,
        current_temple_name=title,
    )


    # ==================================================
    # 13. EXTRACT FULL TEXT
    # ==================================================

    for element in soup.select(
        "script, style, noscript, svg, nav, footer, "
        "header, aside, iframe"
    ):
        element.decompose()

    for comment in soup.find_all(
        string=lambda text: isinstance(text, Comment)
    ):
        comment.extract()

    full_text = "\n".join(
        clean(line)
        for line in soup.get_text(
            separator="\n", strip=True
        ).splitlines()
        if clean(line)
    )


    # ==================================================
    # 14. REFERENCES
    # ==================================================

    references = [{
        "title": title,
        "url": page_url,
        "publisher": "Shaivam.org"
    }]

    for obj in objects:
        citation = obj.get("citation")

        if isinstance(citation, str):
            references.append({
                "title": citation,
                "url": None
            })

        elif isinstance(citation, list):
            for item in citation:
                if isinstance(item, str):
                    references.append({
                        "title": item,
                        "url": None
                    })


    # ==================================================
    # 15. BUILD FINAL JSON
    # ==================================================

    data = {
        "id": temple_id,
        "title": title,
        "shortDescription": short_description,
        "categories": categories,
        "tags": tags,
        "url": page_url,
        

        "location": {
            "latitude": latitude,
            "longitude": longitude,

            "address": {
                "city": city,
                "district": district,
                "state": state,
                "country": country
            },

            "maps": {
                "provider": maps_provider,
                "url": maps_url
            }
        },

        "content": {
            "fullText": full_text,
            "timings": timings,
            "nearbyTemples": nearby_temples
        },

        "images": images,
        "links": links,
        "references": references
    }


    return data


def load_urls(filename):
    """Read one URL per line; ignore blank lines and # comments."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(path, "r", encoding="utf-8") as file:
        urls = []
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(urls))


def main():
    try:
        urls = load_urls(URLS_FILE)
    except OSError as error:
        raise SystemExit(f"Cannot read {URLS_FILE}: {error}")

    if not urls:
        raise SystemExit(f"No URLs found in {URLS_FILE}")

    results = []
    failures = []
    for index, url in enumerate(urls, start=1):
        print(f"\n[{index}/{len(urls)}]", end=" ")
        try:
            data = scrape_temple(url)
            if data:
                results.append(data)
                print(f"  OK: {data.get('title') or url}")
            else:
                failures.append(url)
        except Exception as error:
            print(f"  ERROR processing {url}: {error}")
            failures.append(url)
        # Polite delay between requests to avoid triggering rate-limits.
        if index < len(urls):
            time.sleep(random.uniform(2, 5))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=4)

    print(f"\nJSON created: {OUTPUT_FILE}")
    print(f"Successful temples: {len(results)} / {len(urls)}")
    if failures:
        print(f"Failed URLs ({len(failures)}):")
        for url in failures:
            print(" -", url)


if __name__ == "__main__":
    main()

