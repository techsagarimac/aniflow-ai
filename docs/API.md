# AniFlow API

Base URL: `http://127.0.0.1:8000/api`

Authenticate with `Authorization: Bearer <token>` after login.

Interactive docs: `/docs`.

## Auth

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/login` | `{ email, password }` → `{ access_token, user }` |
| GET | `/auth/me` | Current user |

## Production

| Method | Path |
|---|---|
| GET/POST | `/projects` |
| GET/PATCH/DELETE | `/projects/{id}` |
| GET | `/projects/{id}/characters` |
| GET/POST | `/episodes` |
| GET/PATCH | `/episodes/{id}` |
| GET/POST | `/scenes` |
| GET/PATCH | `/scenes/{id}` |
| POST | `/scenes/{id}/advance` |
| GET/POST | `/tasks` |
| GET/PATCH | `/tasks/{id}` |
| GET | `/artists` |
| GET | `/artists/{id}` |
| GET | `/users` |

## Reviews & files

| Method | Path |
|---|---|
| GET/POST | `/reviews` |
| GET/POST | `/revisions` |
| PATCH | `/revisions/{id}` |
| GET/POST | `/files/scene/{scene_id}` |
| GET | `/files/versions/{id}/download` |
| GET/POST | `/scenes/{id}/comments` |

## Intelligence

| Method | Path |
|---|---|
| GET | `/dashboard` |
| GET | `/calendar` |
| GET | `/search` |
| GET | `/analytics` |
| GET | `/notifications` |
| POST | `/ai/schedule` |
| POST | `/ai/bottlenecks` |
| POST | `/ai/assignment-recommendation` |
| POST | `/ai/risk-analysis` |
| POST | `/ai/chat` |
| GET | `/ai/analyses` |
| POST | `/ai/analyses/{id}/approve` |
