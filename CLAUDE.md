# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Receipt Expense Tracker — a lightweight web app that uploads receipts (JPG/PNG/PDF), parses them via **Upstage Vision LLM** through LangChain, and stores structured expense data in a JSON file. No database is used in the MVP.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18+, Vite 5+, TailwindCSS 3+, Axios, React Router |
| Backend | Python FastAPI 0.111+, LangChain 0.2+, langchain-upstage |
| OCR LLM | `document-digitization-vision` (Upstage) |
| Image processing | Pillow, pdf2image (requires Poppler) |
| Storage | `backend/data/expenses.json` (append-only JSON array) |
| Deployment | Vercel (frontend static build + backend serverless via Mangum) |

## Planned Directory Structure

```
receipt-tracker/
├── frontend/
│   ├── src/
│   │   ├── pages/          # Dashboard.jsx, UploadPage.jsx, ExpenseDetail.jsx
│   │   ├── components/     # DropZone, ParsePreview, ExpenseCard, SummaryCard, FilterBar, Badge, Modal, Toast
│   │   └── api/axios.js    # Axios instance, baseURL from VITE_API_BASE_URL
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── main.py             # FastAPI app, CORS, router registration
│   ├── routers/
│   │   ├── upload.py       # POST /api/upload
│   │   ├── expenses.py     # GET/DELETE/PUT /api/expenses
│   │   └── summary.py      # GET /api/summary
│   ├── services/
│   │   ├── ocr_service.py      # LangChain + ChatUpstage + JsonOutputParser
│   │   └── storage_service.py  # load/save/append expenses.json
│   ├── data/expenses.json
│   └── requirements.txt
├── vercel.json
└── README.md
```

## Development Commands

### Backend
```bash
# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash

# Install dependencies
pip install -r backend/requirements.txt

# Start dev server (from repo root)
uvicorn backend.main:app --reload
# → http://localhost:8000/docs (Swagger UI)
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # → http://localhost:5173
npm run build      # Production build to dist/
```

## Environment Variables

Create `backend/.env`:
```
UPSTAGE_API_KEY=up_xxx...
DATA_FILE_PATH=backend/data/expenses.json   # Omit on Vercel; auto-uses /tmp/expenses.json when VERCEL=1
```

Create `frontend/.env.local`:
```
VITE_API_BASE_URL=http://localhost:8000
```

On Vercel, only `UPSTAGE_API_KEY` needs to be set manually. `VITE_API_BASE_URL` should be empty (same-domain relative path), and `DATA_FILE_PATH` is handled automatically.

## Architecture Decisions

**OCR pipeline**: File upload → Pillow/pdf2image converts to Base64 → `ChatUpstage` vision model called via LangChain Chain → `JsonOutputParser` extracts structured JSON → UUID assigned → appended to `expenses.json`.

**Data persistence on Vercel**: Vercel serverless does not persist the file system between invocations. MVP solution is `localStorage` on the client mirroring the JSON data. For stable persistence, deploy the backend to Railway/Render or migrate to Vercel KV / Supabase.

**Vercel routing**: `/api/*` routes to `backend/main.py` (wrapped with Mangum for ASGI compatibility); all other routes serve the frontend static build.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload` | Upload receipt file, returns parsed JSON |
| GET | `/api/expenses` | List expenses; supports `?from=&to=` date filter |
| DELETE | `/api/expenses/{id}` | Delete by UUID |
| PUT | `/api/expenses/{id}` | Partial update by UUID |
| GET | `/api/summary` | Totals and per-category breakdown; supports `?month=YYYY-MM` |

## Data Schema (expenses.json entry)

```json
{
  "id": "uuid-v4",
  "created_at": "ISO8601",
  "store_name": "string",
  "receipt_date": "YYYY-MM-DD",
  "receipt_time": "HH:MM | null",
  "category": "식료품|외식|교통|쇼핑|의료|기타",
  "items": [{ "name": "", "quantity": 0, "unit_price": 0, "total_price": 0 }],
  "subtotal": 0,
  "discount": 0,
  "tax": 0,
  "total_amount": 0,
  "payment_method": "string | null",
  "raw_image_path": "uploads/filename"
}
```

## Design System

- **Colors**: Primary `indigo-600`, background `gray-50`, surface `white`
- **Font**: Pretendard (CDN) → Noto Sans KR fallback
- **Layout**: `max-w-4xl mx-auto`, sticky header `h-16`, mobile-first grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`)
- **Animations**: Custom keyframes in `tailwind.config.js` — `slide-up` (Toast), `scale-in` (Modal), `fade-in` (page transition)
- **Category badge colors**: green=식료품, orange=외식, blue=교통, purple=쇼핑, red=의료, gray=기타
