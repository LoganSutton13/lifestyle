# Lifestyle

A mobile-first health and fitness coaching Progressive Web App (PWA) with client, coach, and admin roles. Clients track meal plans, daily checklists, workouts (freestyle and assigned), body measurements, and profile settings. Coaches manage associated clients, exercise templates, and workout assignments. Admins manage accounts and the global exercise catalog.

## Tech Stack

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, TanStack Query, React Hook Form, Zod, Recharts, lucide-react, vite-plugin-pwa
- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2.x async, Alembic, Pydantic, Argon2 (pwdlib), JWT
- **Database:** PostgreSQL (Neon Free for MVP)
- **Hosting:** Vercel (frontend + backend), Railway fallback for backend

## Folder Structure

```txt
lifestyle/
  backend/          # FastAPI API (one SQLAlchemy model class per file)
  frontend/         # React PWA
  docs/             # Build specification
```

## Local Setup

### Prerequisites

- Node.js LTS, npm, Python 3.12+, Git, PostgreSQL (local or Docker)

### Install

```bash
git clone <repo-url>
cd lifestyle

cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install aiosqlite pytest pytest-asyncio httpx

cd ../frontend
npm install
```

### Backend environment

Copy `backend/.env.example` to `backend/.env` and adjust:

```txt
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://localhost:5432/fitness_app_dev
DB_POOL_MODE=persistent
JWT_SECRET=local-dev-secret-change-this
ACCESS_TOKEN_MINUTES=15
REFRESH_TOKEN_DAYS=30
CORS_ORIGINS=http://localhost:5173
COOKIE_SECURE=false
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=ChangeMe12345
```

### Frontend environment

Copy `frontend/.env.local.example` to `frontend/.env.local`:

```txt
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Database

```bash
createdb fitness_app_dev   # or create via Docker/pgAdmin

cd backend
alembic upgrade head
python -m app.scripts.seed_reference_data
python -m app.scripts.create_initial_admin
```

### Run locally

```bash
# Terminal 1 - backend
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - frontend
cd frontend
npm run dev
```

Visit http://localhost:5173

## Environment Variables

| Backend | Description |
| --- | --- |
| `DATABASE_URL` | Async Postgres URL (`postgresql+asyncpg://...`) |
| `JWT_SECRET` | Min 32-byte secret for access tokens |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `COOKIE_SECURE` | `false` local, `true` production |
| `DB_POOL_MODE` | `serverless` on Vercel, `persistent` on Railway |

| Frontend | Description |
| --- | --- |
| `VITE_API_BASE_URL` | Backend API base URL |

## Tests

```bash
cd backend && python -m pytest tests/ -v
cd frontend && npm test
```

## Deploy Backend (Vercel)

1. Create Vercel project with root directory `backend`
2. Set env vars (see spec section 15.5)
3. Use `DB_POOL_MODE=serverless` with Neon pooled URL
4. Run migrations against production DB before first use
5. Verify: `https://<backend>.vercel.app/api/health`

## Deploy Frontend (Vercel)

1. Create Vercel project with root directory `frontend`
2. Set `VITE_API_BASE_URL` to backend URL
3. Build: `npm run build`, output: `dist`

## Railway Backend Fallback

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set `DB_POOL_MODE=persistent` and update frontend `VITE_API_BASE_URL`.

## PWA Icons

Required in `frontend/public/icons/`:

- `favicon.svg`, `icon-192.png`, `icon-512.png`, `maskable-512.png`, `apple-touch-icon.png`

12 food-character avatars live in `frontend/public/avatars/`.

## Known Limitations

Samsung/Galaxy Watch direct PWA integration is **not** included in MVP. Manual measurement entry is supported; `source` fields are extensible for future Health Connect sync.

## Troubleshooting

- **401 on API calls:** Check `VITE_API_BASE_URL` and CORS_ORIGINS match your frontend URL
- **Cookie refresh fails cross-domain:** Set `COOKIE_SECURE=true`, `SameSite=None` (handled when secure)
- **Alembic errors:** Ensure `DATABASE_URL` uses `postgresql+asyncpg://` format
- **CITEXT on Postgres:** Initial migration enables `citext` extension; username uniqueness is case-insensitive
