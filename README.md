# TrackForge

A Jira-style issue tracker — built with a **FastAPI** backend, **PostgreSQL** database, and a
**Flask** (Python) frontend. No containers, CI, or deployment config included on purpose —
that part is left for you to add later (DevOps phase).

## Architecture

```
trackforge/
├── backend/                FastAPI REST API + SQLAlchemy models + Postgres
│   ├── app/
│   │   ├── core/            config, db session, security (JWT + bcrypt), deps
│   │   ├── models/          SQLAlchemy ORM models
│   │   ├── schemas/         Pydantic request/response schemas
│   │   ├── routers/         auth, projects, issues, comments, labels, dashboard
│   │   └── main.py
│   ├── tests/                pytest test suite
│   ├── requirements.txt
│   └── .env.example
└── frontend/                Flask server-rendered UI (Jinja2 + plain CSS/JS)
    ├── templates/
    ├── static/css/
    ├── app.py
    ├── requirements.txt
    └── .env.example
```

## Features

**Core**
- JWT auth (register / login / `me`) with bcrypt password hashing
- Projects with unique keys (e.g. `TF`) and project members (admin/member roles)
- Issues with type (bug/task/story/epic), priority, status, assignee — auto-numbered keys like `TF-1`, `TF-2`
- Kanban board view (To Do / In Progress / In Review / Done)
- Comments on issues

**Added in this round**
- **Due dates** on issues
- **Labels** per project (create / list / delete, color-coded)
- **Activity log** — every field change on an issue is recorded with who changed what
- **Search & filter** — search issues by title, filter by status/priority/assignee
- **Pagination** on the issues list endpoint
- **Dashboard** per project — total issues, breakdown by status/priority, overdue count
- **Rate limiting** on login (5/minute) via `slowapi` to slow down brute-force attempts
- **Global exception handler** — backend never leaks stack traces, returns clean JSON errors
- **Frontend resiliency** — centralized API call wrapper with timeouts, auto-logout on expired session, custom 404/500 pages
- **Responsive UI** — mobile-first navbar, horizontally-scrollable Kanban board on small screens, fluid spacing, touch-friendly inputs
- **Pytest test suite** for auth endpoints

## 1. Set up PostgreSQL

```bash
createdb trackforge
psql -c "CREATE USER trackforge WITH PASSWORD 'trackforge';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE trackforge TO trackforge;"
```

Or point `DATABASE_URL` at any Postgres instance you already have.

> Note: new columns (e.g. `due_date`) and new tables (`labels`, `issue_labels`, `activity_logs`)
> are only created automatically for a **fresh** database, since `Base.metadata.create_all()`
> doesn't alter existing tables. If you already had the DB running before these features were
> added, drop and recreate it (or set up Alembic migrations) to pick up the schema changes.

## 2. Run the backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit DATABASE_URL / SECRET_KEY as needed
export DATABASE_URL="postgresql+psycopg2://trackforge:trackforge@localhost:5432/trackforge"
export SECRET_KEY="some-long-random-string"

uvicorn app.main:app --reload --port 8000
```

Tables are auto-created on startup. API docs: http://localhost:8000/docs

### Run backend tests

```bash
cd backend
pytest tests
```

## 3. Run the frontend

```bash
cd frontend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit values as needed
export API_BASE_URL="http://localhost:8000/api"
export FRONTEND_SECRET_KEY="another-long-random-string"
export API_TIMEOUT_SECONDS="5"

python app.py
```

Visit http://localhost:5000 — sign up, create a project, start adding issues.

## API Overview

| Area       | Endpoints |
|------------|-----------|
| Auth       | `POST /api/auth/register`, `POST /api/auth/login` (rate-limited), `GET /api/auth/me` |
| Projects   | `POST /api/projects`, `GET /api/projects`, `GET /api/projects/{id}`, `POST /api/projects/{id}/members`, `GET /api/projects/{id}/members` |
| Issues     | `POST /api/projects/{id}/issues`, `GET /api/projects/{id}/issues` (search/filter/pagination), `GET /{issue_id}`, `PATCH /{issue_id}`, `DELETE /{issue_id}`, `GET /{issue_id}/activity` |
| Labels     | `POST /api/projects/{id}/labels`, `GET /api/projects/{id}/labels`, `DELETE /api/projects/{id}/labels/{label_id}` |
| Comments   | `POST /api/issues/{id}/comments`, `GET /api/issues/{id}/comments` |
| Dashboard  | `GET /api/projects/{id}/dashboard` |
| Health     | `GET /api/health` |

## Notes for later (DevOps — intentionally left out)

When you're ready, you can add: Dockerfiles for backend/frontend, docker-compose with a
Postgres service, Alembic migrations (folder already has the dependency, just needs
`alembic init`), Nginx reverse proxy, CI/CD pipeline (e.g. running the pytest suite on push),
and environment-based secrets management.