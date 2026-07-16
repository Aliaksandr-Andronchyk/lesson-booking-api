# Lesson Booking API

![CI](https://github.com/SashaAndronchyk/lesson-booking-api/actions/workflows/ci.yml/badge.svg)

REST API for tutors to manage lesson bookings — a compact but production-shaped demo service.

**Stack:** FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL (asyncpg) · Alembic · Docker Compose · pytest · GitHub Actions

## Features

- **Tutors** — CRUD with unique-email guard (409 on duplicates), pagination, subject filter
- **Lessons** — booking with business rules:
  - time-slot **overlap detection** per tutor (409 on conflict; back-to-back slots allowed)
  - cancelled slots can be rebooked
  - status lifecycle `scheduled → completed | cancelled` with guarded transitions
  - filters: tutor, status, date range; limit/offset pagination
- Async SQLAlchemy 2.0 (`Mapped` / `mapped_column` typing), Alembic migrations
- Tests run against **both** in-memory SQLite (fast local loop) and real PostgreSQL (CI)
- OpenAPI docs out of the box at `/docs`

## Run with Docker

```bash
docker compose up --build
```

API is on http://localhost:8000, interactive docs on http://localhost:8000/docs.
Migrations are applied automatically on startup.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # point DATABASE_URL to your PostgreSQL
alembic upgrade head
uvicorn app.main:app --reload
```

## Tests

```bash
pytest -v                     # in-memory SQLite, no infra needed
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/lessons_test pytest -v
```

CI (GitHub Actions) lints with ruff, applies migrations to a real PostgreSQL 16 service
container, and runs the suite against both PostgreSQL and SQLite.

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/tutors` | Create tutor (409 on duplicate email) |
| GET | `/tutors` | List tutors (`limit`, `offset`, `subject`) |
| GET | `/tutors/{id}` | Get tutor |
| DELETE | `/tutors/{id}` | Delete tutor (cascades lessons) |
| POST | `/lessons` | Book lesson (409 on slot overlap) |
| GET | `/lessons` | List lessons (`tutor_id`, `status`, `starts_after`, `starts_before`) |
| GET | `/lessons/{id}` | Get lesson |
| PATCH | `/lessons/{id}/cancel` | Cancel (blocked for completed) |
| PATCH | `/lessons/{id}/complete` | Complete (scheduled only) |
| GET | `/health` | Health probe |

## Project layout

```
app/
  main.py        # app wiring
  config.py      # pydantic-settings
  database.py    # async engine/session, declarative base
  models.py      # SQLAlchemy 2.0 models
  schemas.py     # pydantic v2 schemas
  routers/       # tutors, lessons
alembic/         # migrations (async env)
tests/           # pytest + httpx, DB-agnostic fixtures
```
