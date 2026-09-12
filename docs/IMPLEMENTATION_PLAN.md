# AniFlow AI — Implementation Plan

## Product

AniFlow AI is a software-only SaaS platform for anime/animation studios. It centralizes scene tracking, artist workload, revisions, reviews, and production risk. AI assists production managers with scheduling, bottleneck detection, assignment recommendations, and risk scoring. AI never auto-assigns work.

## Architecture

```
┌─────────────┐     JWT      ┌──────────────┐     SQLAlchemy     ┌────────────┐
│ React + Vite│ ───────────► │ FastAPI API  │ ─────────────────► │ PostgreSQL │
│ TypeScript  │   REST /api  │ Pydantic     │                    │ or SQLite  │
└─────────────┘              └──────┬───────┘                    └────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              AIService       LocalStorage     Notification
              Mock | LLM      (cloud-ready)    Service
```

- Frontend talks only to `/api/*`. Business logic stays on the backend.
- `AIService` is an interface. `MockAIService` is default when `AI_API_KEY` is unset. `LLMAIService` calls an OpenAI-compatible endpoint.
- `StorageService` writes to `STORAGE_DIR` locally; S3/GCS can implement the same interface later.

## Data model (core relations)

- `User` (role: admin | production_manager | director | artist | reviewer)
- `ArtistProfile` 1–1 `User`
- `Project` → `Episode` → `Scene`
- `Scene` ↔ `Character` (M2M), `Scene.assigned_artist_id` → `User`
- `Task` optional FKs to project/episode/scene + assignee
- `FileAsset` → `FileVersion` (never overwrite)
- `Review` + `RevisionRequest` + `Comment` on scenes/versions
- `ProductionMilestone`, `Notification`
- `AIAnalysis`, `RiskAssessment` persist AI outputs for the dashboard

## Auth & RBAC

- JWT access tokens (`SECRET_KEY`, expire via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Passwords hashed with bcrypt
- Role matrix (enforced in API dependencies, mirrored in UI):
  - Admin: full
  - Production Manager: projects, episodes, scenes, tasks, artists, schedules
  - Director: review production, approve AI recommendations
  - Artist: assigned work, uploads, progress, respond to revisions
  - Reviewer: reviews + revision requests

## Phases

| Phase | Scope | Exit criteria |
|-------|--------|----------------|
| 1 | Config, models, DB, JWT auth, FastAPI app, Vite+Tailwind shell, layout, login | Login works; protected routes redirect |
| 2 | CRUD: projects, episodes, scenes, tasks, artists | Seeded Project Sakura listable via API + UI |
| 3 | Dashboard, scene Kanban, calendar, reviews, versions | Scene 042 version/review flow works |
| 4 | AI schedule, bottlenecks, assignment recs, risk score | Mock AI returns realistic Episode 07 risk |
| 5 | AniFlow Assistant chat, analytics, notifications | Chat answers from DB; charts render |
| 6 | Tests, rate limits, Docker, README, demo seed polish | `pytest` + frontend tests pass; docker-compose up |

## Local defaults

- Backend: `http://localhost:8000` (SQLite if `DATABASE_URL` unset)
- Frontend: `http://localhost:5173` (proxies `/api` to backend)
- Demo users all share password `demo1234` (documented in README)

## Demo narrative (Project Sakura)

Original fiction. 12 episodes: 01–03 completed, 04 QC, 05 compositing, 06 animation, **07 animation HIGH RISK**, 08 storyboard, 09–12 planning. 100+ scenes, 10 artists, overdue tasks, revision history on Scene 042.

## Non-goals

- Cloud object storage in v1
- Real-time WebSockets (polling/refetch is enough)
- Replacing artists or auto-reassigning work
