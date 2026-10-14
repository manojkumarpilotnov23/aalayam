
import requests
import csv
import json
import io
from pathlib import Path

# Configuration file
CONFIG_FILE = "spreadsheet_id.json"

# Output directory
OUTPUT_DIR = Path("json_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def export_worksheet(spreadsheet_id, worksheet_name, gid):

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

    # First row contains headers
    headers = rows[0]

    # Convert rows into JSON objects
    json_data = []

    for row in rows[1:]:

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

        print(f"Processing: {name} (GID: {gid})")

        try:
            output_file, record_count = export_worksheet(
                spreadsheet_id,
                name,
                gid
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

