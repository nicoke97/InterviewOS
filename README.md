# Codenda — Kumon × LeetCode × Odoo Interview Trainer

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

# 4. Run (API on :8001, UI on :5174)
npm run dev
```

Open http://localhost:5174

## Production (solo — one user, one database)

Local production smoke test (builds UI, serves API + static on one port):

```bash
npm run start:prod
```

Open http://localhost:8001

### Docker

```bash
docker build -t codenda .
docker run --rm -p 8001:8001 -v codenda-data:/app/data codenda
```

### Fly.io

```bash
fly launch --no-deploy    # link app, keep fly.toml
fly volumes create data --size 1
fly deploy
```

Persist progress: mount a volume at `/app/data` (SQLite lives in `data/progress.db`).

### Environment

Copy `.env.example` to `.env` for local overrides. Key variables:

| Variable | Purpose |
|----------|---------|
| `ENVIRONMENT` | `production` disables dev_mode and enables prod defaults |
| `DATABASE_URL` | SQLite by default; use Postgres when you add multi-user |
| `ALLOWED_ORIGINS` | CORS origins if UI and API are on different domains |
| `APP_SECRET` | Reserved for future auth / billing |
| `SERVE_STATIC` | Serve `frontend/dist` from FastAPI (on in Docker) |

## Daily rhythm

| Slot    | Duration | Content                          |
|----------|----------|----------------------------------|
| Morning | 15 min   | Kumon sheet (8–12 drills)        |
| Evening | 15 min   | Kumon / LeetCode / Interview     |

## Scripts

- `npm run generate-content` — regenerate YAML curriculum
- `npm run validate-content` — validate all content files
- `npm run init-db` — create/reset SQLite database
