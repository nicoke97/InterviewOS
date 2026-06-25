# PythonOS — Kumon × LeetCode × Odoo Interview Trainer

Local-first gamified Python learning app for Odoo Technical Support Engineer interview prep.

## Stack

- **Frontend:** Vite + React + TypeScript + Tailwind CSS v4 + Monaco Editor + Recharts
- **Backend:** FastAPI + SQLite + Python code executor
- **Content:** YAML drills under `content/levels/`

## Quick start

```bash
# 1. Generate curriculum content (first time)
python scripts/generate-content.py

# 2. Install dependencies
cd backend && pip install -e . && cd ..
cd frontend && npm install && cd ..
npm install

# 3. Initialize database
python scripts/init-db.py

# 4. Run (API on :8000, UI on :5173)
npm run dev
```

Open http://localhost:5173

## Daily rhythm

| Slot    | Duration | Content                          |
|---------|----------|----------------------------------|
| Morning | 15 min   | Kumon sheet (8–12 drills)        |
| Evening | 15 min   | Kumon / LeetCode / Interview     |

## Scripts

- `npm run generate-content` — regenerate YAML curriculum
- `npm run validate-content` — validate all content files
- `npm run init-db` — create/reset SQLite database
