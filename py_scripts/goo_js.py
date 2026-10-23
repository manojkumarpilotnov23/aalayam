
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

    print(f"  [image] Total unique map URLs: {len(unique_urls)}")
    print(f"  [image] Already cached: {len(unique_urls) - len(pending_urls)}, pending: {len(pending_urls)}")

    if not pending_urls:
        print("  [image] All URLs already cached, skipping Playwright.")
        return IMAGE_CACHE

    try:
        print("  [image] Launching Playwright Chromium (headless)…")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1365, "height": 900})
            print(f"  [image] Browser launched. Processing {len(pending_urls)} URL(s)…")

            for i, url in enumerate(pending_urls, 1):
                print(f"  [image] ({i}/{len(pending_urls)}) Navigating to: {url}")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    print(f"  [image]   domcontentloaded — waiting 5 s for page to settle…")
                    page.wait_for_timeout(5000)

                    page_title = page.title()
                    print(f"  [image]   Page title: {page_title!r}")

                    all_images = page.evaluate("""() => {
                        return Array.from(document.images).map(img => ({
                            src: img.currentSrc || img.src,
                            width: img.getBoundingClientRect().width,
                            height: img.getBoundingClientRect().height,
                            top: img.getBoundingClientRect().top,
                            left: img.getBoundingClientRect().left,
                        }));
                    }""")
                    print(f"  [image]   Total <img> elements on page: {len(all_images)}")
                    for idx, img in enumerate(all_images[:10]):
                        print(f"  [image]   img[{idx}] {img['width']:.0f}x{img['height']:.0f} src={img['src'][:80]}")

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

                    if image_url:
                        print(f"  [image]   FOUND image: {image_url[:100]}")
                    else:
                        print(f"  [image]   No matching image found (googleusercontent / ggpht, >100px, in viewport).")

                    IMAGE_CACHE[url] = image_url

                except Exception as error:
                    print(f"  [image]   ERROR extracting image for {url}: {error}")
                    IMAGE_CACHE[url] = None

            browser.close()
            print("  [image] Browser closed.")

    except Exception as error:
        print(f"  [image] Playwright startup error: {error}")
        for url in pending_urls:
            IMAGE_CACHE.setdefault(url, None)

    return IMAGE_CACHE


def export_worksheet(spreadsheet_id, worksheet_name, gid, group_by=None):

    # Build CSV export URL
    csv_url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{spreadsheet_id}/export?format=csv&gid={gid}"
    )
    print(f"  [csv] Downloading: {csv_url}")

    # Download worksheet data
    response = requests.get(csv_url, timeout=60)
    print(f"  [csv] HTTP {response.status_code}, content-length: {len(response.content)} bytes")
    response.raise_for_status()
    response.encoding = "utf-8"

    # Parse CSV
    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)
    print(f"  [csv] Total rows (including header): {len(rows)}")

    if not rows:
        raise ValueError("Worksheet is empty")

    # First row is headers, second row is metadata — skip both
    headers = rows[0]
    print(f"  [csv] Headers ({len(headers)}): {headers}")

    # Convert rows into JSON objects
    json_data = []

    for row_idx, row in enumerate(rows[2:], start=3):

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

    print(f"  [csv] Non-empty data rows: {len(json_data)}")

    # Compute output path (needed for cache preload and final save)
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in worksheet_name)
    output_file = OUTPUT_DIR / f"{safe_name}.json"

    # Find Google Maps links in each record
    map_urls = []

    for record in json_data:
        for key, value in record.items():
            if is_google_maps_url(value):
                print(f"  [maps] Found Maps URL in column '{key}': {value.strip()}")
                map_urls.append(value.strip())

    # Extract images for unique Maps URLs
    if map_urls:
        # Seed IMAGE_CACHE from the existing output so already-resolved URLs skip Playwright
        if output_file.exists():
            with open(output_file, encoding="utf-8") as f:
                for entry in json.load(f):
                    for rec in (entry.get("items", [entry]) if group_by else [entry]):
                        if rec.get("image"):
                            for v in rec.values():
                                if is_google_maps_url(v):
                                    IMAGE_CACHE.setdefault(v.strip(), rec["image"])
                                    break
            print(f"  [cache] Preloaded {len(IMAGE_CACHE)} cached image(s) from existing output.")

        print(f"  [maps] {len(map_urls)} Google Maps link(s) found — starting image extraction…")
        extract_images(map_urls)

        # Add image field to matching records
        matched = 0
        for record in json_data:
            for value in record.values():

                if is_google_maps_url(value):
                    map_url = value.strip()
                    img = IMAGE_CACHE.get(map_url)
                    record["image"] = img
                    if img:
                        matched += 1
                    else:
                        print(f"  [maps] No image resolved for: {map_url}")
                    break

        print(f"  [maps] Image field set: {matched}/{len(map_urls)} resolved.")
    else:
        print("  [maps] No Google Maps URLs found in this worksheet.")

    # Group rows by a column if requested
    if group_by:
        if group_by not in headers:
            raise ValueError(f"group_by column '{group_by}' not found in headers")

        print(f"  [group] Grouping by column: '{group_by}'")
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
        print(f"  [group] {len(json_data)} group(s) created.")

    # Save JSON
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            json_data,
            file,
            ensure_ascii=False,
            indent=4
        )

    print(f"  [out] Written to: {output_file}")
    return output_file, len(json_data)


def main():

    # Load configuration
    print(f"Loading config from: {CONFIG_FILE}")
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

        print(f"{'='*50}")
        print(f"Processing: {name} (GID: {gid}, group_by: {group_by!r})")
        print(f"{'='*50}")

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
            import traceback
            print(f"FAILED: {error}")
            traceback.print_exc()
            print()
            failed += 1

    print("=" * 40)
    print(f"Successful: {success}")
    print(f"Failed: {failed}")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
