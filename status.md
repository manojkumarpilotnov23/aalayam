# Status Log

## 2026-10-15

### UI
- Changed app font to **Arima Madurai** (replaces Inter + Noto Sans Tamil) — applies globally including Tamil text
- Added `onError` fallback on temple card and item card images — broken/failed image URLs fall back to the 🛕 placeholder instead of showing a broken image icon
- Added `loading="lazy"` on all `<img>` tags for performance

### Maps — in-app embed
- Replaced all "Open in Maps" external links with a **MapModal** component (`ui/src/components/MapModal.tsx`)
- Clicking "View Map" now opens an in-app modal with a Google Maps `<iframe>` — no new tab
- Modal shows a loading state while the embed URL is being resolved, and falls back to an external link if resolution fails

### Backend
- Added `GET /maps/embed?url=` endpoint to `main.py`
- Endpoint follows the `maps.app.goo.gl` short URL redirect server-side, extracts coordinates (`@lat,lng`) from the resolved Google Maps URL, and returns an embeddable `maps.google.com/?output=embed` URL
- Added `fetchMapEmbed(locationUrl)` to `ui/src/api.ts`

## 2026-10-23

### UI
- **Edit page** (`/edit`) — select a temple from dropdown, edit all fields, save back to `Manoj.json` via PUT
- **Rich-text editor** (`ContentEditor`) — Tiptap editor with Bold / Italic / H2 / H3 / Bullet list toolbar
- **HTML rendering** — Tiptap HTML fields render correctly in TempleDetail; accordion header and card previews use `stripHtml()`
- **Show all temples** — TempleList fetches up to 200 results (was 20)

### Backend
- Added `PUT /temples/{temple_id}` endpoint — patches temple fields in `Manoj.json` and reloads in-memory cache

### Scripts
- `goo_js.py` — added detailed per-step debug logs (`[csv]`, `[maps]`, `[image]`, `[cache]`, `[group]`)
- `goo_js.py` — skips Playwright browser call for map URLs that already have an image in the existing output JSON
