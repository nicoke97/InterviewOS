# Codenda — SDE II trainer (cola + Codi)

Local-first interview trainer: adaptive SDE program (theory queue, weighted flashcards, Kumon-style algorithm sets with a completed/failed pool) plus optional Kumon tracks. Codi is the coach — incomplete is a light day, not a punishment; fail a pooled problem and you drop back to rungs.

## Stack

- **Frontend:** Vite + React + TypeScript + Tailwind CSS v4 + Monaco Editor + Recharts
- **Backend:** FastAPI + SQLite + Python code executor
- **Content:** SDE program under `content/sde/`; Kumon YAML under `content/levels/`

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

## Daily rhythm (SDE program — default)

The engine picks the day. You do not follow a calendar date.

| Block | What |
|-------|------|
| Cards | Up to 40 *distinct* cards, weighted random. No duplicates in one session. Light day: fewer cards. |
| Pool | One random *completed* algorithm, full. Failed pool first. Miss twice → restart day-1 rungs. |
| Active algo | Day 1: rung1×5 + rung2×5 + rung3×5 + full×2. Day 2: one full; pass → pool, start next algo with rung1×5 only. |
| Theory | Only if code day was not light: read + quiz + new cards the same day. |
| Voice | After C# (or Python) day-2 pass: speak the “why”, transcribe, approve or block the next language. |
| Off / offline | Light day, not punishment. Warm-up = last sheet you actually touched. Offline needs a quiz when you return. |

Study contract: [`plan-estudios.md`](plan-estudios.md).

## Scripts

- `python scripts/generate_sde_content.py` — regenerate SDE theory/algorithm YAML
- `npm run generate-content` — regenerate YAML curriculum
- `npm run validate-content` — validate all content files
- `npm run init-db` — create/reset SQLite database
