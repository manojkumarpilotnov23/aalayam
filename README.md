# aalayam
Repo to share the location specific details of temples starting from kudavayil books

## Local Development

### Prerequisites
- Python 3.9+
- Node.js 18+

### Backend (FastAPI)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server (runs on http://localhost:8000)
python3 -m uvicorn main:app --reload
```

API endpoints:
- `GET /temples` — list temples (supports `?q=`, `?tags=`, `?skip=`, `?limit=`)
- `GET /temples/{id}` — temple detail
- `GET /tags` — all available tags

### Frontend (React + Vite)

```bash
cd ui

# Install dependencies
npm install

# Start dev server (runs on http://localhost:5173)
npm run dev
```

The frontend reads `VITE_API_URL` from `.env.local` (already set to `http://localhost:8000`).

### Build for production

```bash
cd ui
npm run build
# Output is in ui/dist/
```

## Data Pipeline

Temple data is pulled from Google Sheets into `py_scripts/json_output/`:

```bash
cd py_scripts
pip install -r ../requirements.txt
python goo_js.py
```
