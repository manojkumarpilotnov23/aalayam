import json
import os
import glob
import re
import urllib.request
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Aalayam Temple API",
    description="REST API for Tamil Hindu temple data",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "PUT"],
    allow_headers=["*"],
)

_JSON_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "py_scripts", "json_output"
)

_MASTER_FILE = os.path.join(_JSON_OUTPUT_DIR, "Manoj.json")


def _parse_tags(raw) -> list[str]:
    if isinstance(raw, list):
        return [t.strip() for t in raw if isinstance(t, str) and t.strip()]
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []


def _load_temples() -> list[dict]:
    combined: dict[str, dict] = {}
    for filepath in sorted(glob.glob(os.path.join(_JSON_OUTPUT_DIR, "*.json"))):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        for entry in data:
            tid = (entry.get("id") or "").strip()
            if not tid or tid == "ID":
                continue
            for item in entry.get("items", []):
                item["id"] = (item.get("id") or "").strip()
                item["name"] = (item.get("name") or "").strip()
                item["tags"] = _parse_tags(item.get("tags", ""))
            if tid in combined:
                combined[tid]["items"].extend(entry.get("items", []))
            else:
                combined[tid] = {"id": tid, "items": list(entry.get("items", []))}
    return list(combined.values())


TEMPLES: list[dict] = _load_temples()
_INDEX: dict[str, dict] = {t["id"]: t for t in TEMPLES}


def _collect_all_tags() -> list[str]:
    seen: set[str] = set()
    tags: list[str] = []
    for t in TEMPLES:
        for item in t.get("items", []):
            for tag in item.get("tags", []):
                if tag.lower() not in seen:
                    tags.append(tag)
                    seen.add(tag.lower())
    return sorted(tags)


ALL_TAGS = _collect_all_tags()


def _reload():
    global TEMPLES, _INDEX, ALL_TAGS
    TEMPLES = _load_temples()
    _INDEX = {t["id"]: t for t in TEMPLES}
    ALL_TAGS = _collect_all_tags()


@app.get("/")
def root():
    return {
        "message": "Aalayam Temple API",
        "endpoints": ["/temples", "/temples/{id}", "/tags", "/maps/embed"],
    }


@app.get("/tags")
def list_tags():
    """Return all unique tags across all temples."""
    return {"tags": ALL_TAGS}


@app.get("/temples")
def list_temples(
    q: str = Query(None),
    tags: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
):
    results = TEMPLES

    if q:
        ql = q.lower()
        results = [
            t for t in results
            if ql in t["id"].lower()
            or any(
                ql in item.get("templeInfo", "").lower()
                or ql in item.get("reference", "").lower()
                or ql in item.get("name", "").lower()
                for item in t.get("items", [])
            )
        ]

    if tags:
        filter_tags = {tag.strip().lower() for tag in tags.split(",") if tag.strip()}
        results = [
            t for t in results
            if any(
                tag.lower() in filter_tags
                for item in t.get("items", [])
                for tag in item.get("tags", [])
            )
        ]

    total = len(results)
    page = results[skip: skip + limit]

    summaries = []
    for t in page:
        items = t.get("items", [])
        first = items[0] if items else {}
        seen: set[str] = set()
        all_tags: list[str] = []
        for item in items:
            for tag in item.get("tags", []):
                if tag.lower() not in seen:
                    all_tags.append(tag)
                    seen.add(tag.lower())
        summaries.append({
            "id": t["id"],
            "name": first.get("name", "").strip(),
            "templeInfo": first.get("templeInfo", ""),
            "reference": first.get("reference", ""),
            "location": first.get("location", ""),
            "tags": all_tags,
            "image": first.get("image"),
            "itemCount": len(items),
        })

    return {"total": total, "skip": skip, "limit": limit, "data": summaries}


@app.get("/maps/embed")
def maps_embed(url: str):
    """Resolve a Google Maps short URL and return an embeddable iframe src."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            final_url = resp.geturl()
        m = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
        if m:
            lat, lng = m.group(1), m.group(2)
            embed = f"https://www.google.com/maps?q={lat},{lng}&output=embed&z=16"
            return {"embedUrl": embed}
    except Exception:
        pass
    return {"embedUrl": None}


@app.get("/temples/{temple_id}")
def get_temple(temple_id: str):
    """Return full details for a single temple."""
    temple = _INDEX.get(temple_id.strip())
    if not temple:
        raise HTTPException(status_code=404, detail=f"Temple '{temple_id}' not found")
    return temple


@app.put("/temples/{temple_id}")
def update_temple(
    temple_id: str,
    payload: dict,
    authorization: Optional[str] = Header(default=None),
):
    admin_token = os.environ.get("ADMIN_TOKEN", "")
    if admin_token and authorization != f"Bearer {admin_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not os.path.exists(_MASTER_FILE):
        raise HTTPException(status_code=500, detail=f"Master file not found: {_MASTER_FILE}")

    with open(_MASTER_FILE, encoding="utf-8") as f:
        data: list[dict] = json.load(f)

    target = next(
        (e for e in data if (e.get("id") or "").strip() == temple_id.strip()),
        None,
    )
    if not target:
        raise HTTPException(status_code=404, detail=f"Temple '{temple_id}' not found")

    item_patch = payload.get("item", {})
    if target.get("items"):
        item = target["items"][0]
        for field in ("name", "templeInfo", "sculptures", "inscriptions", "padhigam", "location", "image", "reference"):
            if field in item_patch:
                val = item_patch[field]
                item[field] = val.strip() if isinstance(val, str) else val
        if "tags" in item_patch:
            item["tags"] = _parse_tags(item_patch["tags"])

    with open(_MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    _reload()

    return {"ok": True, "id": temple_id}
