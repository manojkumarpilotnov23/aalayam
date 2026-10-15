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
