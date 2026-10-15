
import requests
import csv
import json
import io
from pathlib import Path
from playwright.sync_api import sync_playwright

# Configuration file
CONFIG_FILE = "spreadsheet_id.json"

# Output directory
OUTPUT_DIR = Path("json_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Cache extracted image URLs
IMAGE_CACHE = {}


def is_google_maps_url(value):
    """Check whether a cell contains a Google Maps URL."""

    if not isinstance(value, str):
        return False

    value = value.strip().lower()

    return (
        value.startswith("https://") or
        value.startswith("http://")
    ) and any(
        domain in value
        for domain in (
            "maps.app.goo.gl/",
            "google.com/maps",
            "maps.google.com/"
        )
    )


def extract_images(map_urls):
    """Extract map preview images using Playwright (Python)."""

    unique_urls = list(dict.fromkeys(
        url.strip()
        for url in map_urls
        if url and url.strip()
    ))

    pending_urls = [
        url for url in unique_urls
        if url not in IMAGE_CACHE
    ]

    if not pending_urls:
        return IMAGE_CACHE

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1365, "height": 900})

            for url in pending_urls:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(5000)

                    image_url = page.evaluate("""() => {
                        const images = Array.from(document.images);
                        const image = images.find(img => {
                            const src = img.currentSrc || img.src;
                            const rect = img.getBoundingClientRect();
                            return (
                                src &&
                                src.startsWith("https://") &&
                                (
                                    src.includes("googleusercontent.com") ||
                                    src.includes("ggpht.com")
                                ) &&
                                rect.width > 100 &&
                                rect.height > 100 &&
                                rect.bottom > 0 &&
                                rect.right > 0 &&
                                rect.top < window.innerHeight &&
                                rect.left < window.innerWidth
                            );
                        });
                        return image ? (image.currentSrc || image.src) : null;
                    }""")

                    IMAGE_CACHE[url] = image_url

                except Exception as error:
                    print(f"Image extraction failed for {url}: {error}")
                    IMAGE_CACHE[url] = None

            browser.close()

    except Exception as error:
        print(f"Image extraction error: {error}")
        for url in pending_urls:
            IMAGE_CACHE.setdefault(url, None)

    return IMAGE_CACHE


def export_worksheet(spreadsheet_id, worksheet_name, gid, group_by=None):

    # Build CSV export URL
    csv_url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{spreadsheet_id}/export?format=csv&gid={gid}"
    )

    # Download worksheet data
    response = requests.get(csv_url, timeout=60)
    response.raise_for_status()
    response.encoding = "utf-8"

    # Parse CSV
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)

    if not rows:
        raise ValueError("Worksheet is empty")

    # First row is headers, second row is metadata — skip both
    headers = rows[0]

    # Convert rows into JSON objects
    json_data = []

    for row in rows[2:]:

        # Skip completely empty rows
        if not any(value.strip() for value in row):
            continue

        record = {}

        for index, header in enumerate(headers):

            if not header:
                continue

            value = row[index] if index < len(row) else ""
            record[header] = value

        json_data.append(record)

    # Find Google Maps links in each record
    map_urls = []

    for record in json_data:
        for value in record.values():
            if is_google_maps_url(value):
                map_urls.append(value.strip())

    # Extract images for unique Maps URLs
    if map_urls:
        print(f"Found {len(map_urls)} Google Maps links.")

        extract_images(map_urls)

        # Add image field to matching records
        for record in json_data:
            for value in record.values():

                if is_google_maps_url(value):
                    map_url = value.strip()
                    record["image"] = IMAGE_CACHE.get(map_url)
                    break

    # Group rows by a column if requested
    if group_by:
        if group_by not in headers:
            raise ValueError(f"group_by column '{group_by}' not found in headers")

        groups = {}
        order = []

        for record in json_data:
            key = record[group_by]
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(record)

        json_data = [
            {group_by: key, "items": groups[key]}
            for key in order
        ]

    # Create a safe output filename
    safe_name = "".join(
        char if char.isalnum() or char in "-_"
        else "_"
        for char in worksheet_name
    )

    output_file = OUTPUT_DIR / f"{safe_name}.json"

    # Save JSON
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            json_data,
            file,
            ensure_ascii=False,
            indent=4
        )

    return output_file, len(json_data)


def main():

    # Load configuration
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = json.load(file)

    spreadsheet_id = config["spreadsheet_id"]
    worksheets = config["worksheets"]

    success = 0
    failed = 0

    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"Total worksheets: {len(worksheets)}\n")

    for worksheet in worksheets:

        name = worksheet["name"]
        gid = str(worksheet["gid"])
        group_by = worksheet.get("group_by")

        print(f"Processing: {name} (GID: {gid})")

        try:
            output_file, record_count = export_worksheet(
                spreadsheet_id,
                name,
                gid,
                group_by=group_by
            )

            print(f"SUCCESS: {output_file}")
            print(f"Records: {record_count}\n")
            success += 1

        except Exception as error:
            print(f"FAILED: {error}\n")
            failed += 1

    print("=" * 40)
    print(f"Successful: {success}")
    print(f"Failed: {failed}")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
