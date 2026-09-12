# AniFlow AI

AI-powered production management for anime and animation studios.

AniFlow centralizes scene tracking, artist workload, reviews, revisions, and schedule risk. AI assists production managers with estimates and recommendations. It never auto-assigns work and never replaces artists.

---

## Problem

Studio production spans script, storyboard, layout, key animation, in-betweens, backgrounds, color, compositing, and QC. Managers need a single board for:

- Hundreds of scenes and their stage
- Delayed and overdue work
- Artist load and deadline risk
- Versioned artwork and revision loops
- Episode completion estimates that are clearly labeled as AI estimates

---

## Features

- JWT auth with roles: Admin, Production Manager, Director, Artist, Reviewer
- Projects → episodes → scenes, with Kanban movement
- Tasks (list / kanban / calendar)
- Artist roster and workload
- File versioning (never overwrite)
- Reviews and revision requests
- Production calendar
- Dashboard bottlenecks and overdue counts
- AI: schedule estimate, bottleneck detection, assignment recommendation, risk score, AniFlow Assistant
- Analytics (Recharts)
- Notifications
- Mock AI mode when no API key is set

---

## Architecture

```
React (Vite, TypeScript, Tailwind)
        │  REST /api  + JWT
        ▼
FastAPI  ── SQLAlchemy ── PostgreSQL or SQLite
        ├── AIService (Mock | LLM)
        └── LocalStorageService
```

Implementation notes live in `docs/IMPLEMENTATION_PLAN.md`.

---

## Technology stack

| Layer | Stack |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, Lucide, Recharts |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL (production) / SQLite (local default) |
| Auth | JWT, bcrypt, RBAC |
| AI | `AIService` abstraction, OpenAI-compatible LLM or mock |

---

## Installation

```bash
git clone <your-repo>
cd aniflow-ai
cp .env.example .env
```

---

## Environment variables

See `.env.example`. Important keys:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `sqlite:///./aniflow.db` or `postgresql+psycopg://user:pass@host:5432/aniflow` |
| `SECRET_KEY` | JWT signing secret |
| `AI_API_KEY` | Leave empty to use Mock AI |
| `AI_PROVIDER` | `mock` or `openai` |
| `AI_MODEL` / `AI_BASE_URL` | LLM settings |
| `STORAGE_DIR` | Local file storage |
| `SEED_ON_STARTUP` | Seeds Project Sakura when the database is empty |
| `DEMO_PASSWORD` | Password for seeded accounts (default `demo1234`) |

Never commit real API keys.

---

## Database setup

SQLite is the default. On first backend start, tables are created and demo data is seeded.

PostgreSQL:

```bash
createdb aniflow
# set DATABASE_URL in .env
cd backend
source .venv/bin/activate
alembic upgrade head
```

Migrations live in `backend/alembic/`.

---

## Running the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
uvicorn app.main:app --reload --port 8000
```

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000`. Open [http://localhost:5173](http://localhost:5173).

---

## Running with Docker

```bash
docker compose up --build
```

- App: http://localhost:8080
- API: http://localhost:8000/docs

Compose starts PostgreSQL, the API, and the nginx-hosted UI.

---

## Demo accounts

Password for all seeded users: `demo1234`

| Email | Role |
|---|---|
| `manager@aniflow.ai` | Production Manager (Hana Mori) |
| `director@aniflow.ai` | Director (Kenji Hayashi) |
| `artist@aniflow.ai` | Artist / Key Animator (Aki Tanaka) |
| `reviewer@aniflow.ai` | Reviewer (Rina Okabe) |
| `admin@aniflow.ai` | Admin (Yuna Sato) |

Demo show: **Project Sakura** (original fiction, 12 episodes, 100+ scenes). Episode 07 is the high-risk animation bottleneck. Scene 042 is the rooftop revision walkthrough.

### Suggested walkthrough

1. Sign in as the production manager
2. Open the dashboard — Episode 07 high risk
3. Open Episode 07 → bottleneck analysis → manager-approve the recommendation (work is **not** auto-reassigned)
4. Open Scene 042 → version history
5. Sign in as reviewer → request a revision
6. Sign in as Aki → upload a new version
7. Reviewer approves → advance stage → dashboard updates on refresh

---

## API documentation

Interactive: `/docs` (Swagger) and `/redoc`.

Route summary: `docs/API.md`.

---

## AI architecture

`AIService` defines:

- `estimate_schedule()`
- `detect_bottlenecks()`
- `recommend_artist()`
- `calculate_risk()`
- `answer_project_question()`

`MockAIService` is used when `AI_API_KEY` is missing. `LLMAIService` calls an OpenAI-compatible Chat Completions API and falls back to mock on failure.

All estimates are labeled as AI estimates. Redistribution of work always requires a manager click. The assistant answers from the production database, not generic trivia.

---

## Tests

```bash
cd backend && PYTHONPATH=. .venv/bin/pytest
cd frontend && npm test
```

---

## Screenshots

_Add product screenshots here after running the local demo (login, dashboard, Episode 07, Scene 042, assistant)._

---

## Future improvements

- Cloud object storage (S3-compatible `StorageService`)
- Real-time review comments (WebSocket)
- Shot-level drawing review markup
- Studio SSO (SAML/OIDC)
- Deeper historical velocity models for scheduling
