import json
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Aalayam Temple API",
    description="REST API for Tamil Hindu temple data",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_data", "tamil_content.json")

with open(_DATA_FILE, encoding="utf-8") as f:
    TEMPLES: list[dict] = json.load(f)

# Pre-build an id → temple lookup for O(1) detail fetches.
_INDEX: dict[str, dict] = {t["id"]: t for t in TEMPLES}


@app.get("/")
def root():
    return {"message": "Aalayam Temple API", "endpoints": ["/temples", "/temples/{id}"]}


@app.get("/temples")
def list_temples(
    q: str = Query(None, description="Search title or description"),
    category: str = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
):
    """Return a paginated list of temples with summary fields only."""
    results = TEMPLES

    if q:
        q_lower = q.lower()
        results = [
            t for t in results
            if q_lower in t["title"].lower()
            or q_lower in t.get("shortDescription", "").lower()
            or q_lower in t["id"].lower()
            or any(q_lower in tag.lower() for tag in t.get("tags", []))
        ]

    if category:
        cat_lower = category.lower()
        results = [
            t for t in results
            if any(cat_lower in c.lower() for c in t.get("categories", []))
        ]

    total = len(results)
    page = results[skip: skip + limit]

    # Return summary fields only — omit fullText to keep list responses small.
    summaries = [
        {
            "id": t["id"],
            "title": t["title"],
            "shortDescription": t.get("shortDescription", ""),
            "categories": t.get("categories", []),
            "tags": t.get("tags", []),
            "location": t.get("location", {}),
            "thumbnail": t["images"][0] if t.get("images") else None,
        }
        for t in page
    ]

    return {"total": total, "skip": skip, "limit": limit, "data": summaries}


@app.get("/temples/{temple_id}")
def get_temple(temple_id: str):
    """Return full details for a single temple."""
    temple = _INDEX.get(temple_id)
    if not temple:
        raise HTTPException(status_code=404, detail=f"Temple '{temple_id}' not found")
    return temple
