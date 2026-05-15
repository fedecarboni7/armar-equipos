# agents.md — Armar Equipos

Project context and execution rules for AI coding agents (GitHub Copilot, OpenCode, etc.).

---

## Project Overview

**Armar Equipos** is a web application for forming balanced football teams.

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), Pydantic v2, Jinja2
- **Frontend:** Vanilla JavaScript (ES6+), HTML, CSS — no build step, no framework
- **Database:** PostgreSQL (psycopg3) in production; SQLite in-memory for tests
- **Auth:** JWT via PyJWT, session via Itsdangerous
- **AI:** LangChain + Google Gemini
- **Email:** Brevo (sib-api-v3-sdk)
- **Monitoring:** Sentry
- **Package manager:** `uv` with `pyproject.toml`
- **Linter/Formatter:** Ruff
- **Deployment:** Railway (PostgreSQL + app service)
- **CI/CD:** GitHub Actions (`python-app.yml` for tests+lint, `codeql.yml` for security)

---

## Coding Rules

### General
- Write simple, readable code — clarity over cleverness.
- No unnecessary comments; only explain non-obvious logic.
- Do not add documentation unless explicitly requested.
- If something is ambiguous, ask rather than guess.


### Backend (FastAPI)
- Use `async/await` on all endpoints.
- Validate inputs/outputs with Pydantic schemas.
- Raise `HTTPException` for error responses.
- Never hardcode secrets; read from environment variables.

### Frontend (Vanilla JS)
- Files go in `/static/js/`, split by concern (e.g., `api.js`, `ui.js`).
- Use `fetch` for API calls with `try/catch` error handling.
- Use camelCase for variables and functions.
- No build tools, no bundlers, no frameworks.

### Database
- SQLAlchemy async sessions via dependency injection (`get_db`).
- Tests use SQLite in-memory — do not write tests that require Postgres.

### Migrations (Alembic)
- All schema changes go through Alembic — never use `Base.metadata.create_all()` in production code.
- To generate a migration after changing a model: `alembic revision --autogenerate -m "describe change"`
- Always review the generated script in `alembic/versions/` before applying it.
- To apply migrations locally: `alembic upgrade head`
- `alembic/env.py` must import all SQLAlchemy models so autogenerate can detect changes.
- `alembic.ini` reads `DATABASE_URL` from the environment — never hardcode connection strings.
- On first clone, run `alembic upgrade head` to create the full schema from scratch.
- Do not modify existing migration files; always create a new revision to fix issues.

### Dependencies
- Add packages with: `uv add <package>`
- Dev dependencies: `uv add --group dev <package>`

---

## Testing

```bash
# Run all tests except Brevo (default for CI)
uv run pytest -v -m "not brevo"

# Run all tests
uv run pytest -v

# Run a specific file
uv run pytest tests/test_teams.py -v
```

---

## CI Validation Gate

Every change must pass locally before pushing:

```bash
uv run ruff format --check .   # Check formatting
uv run ruff check .            # Lint
uv run pytest -v -m "not brevo"  # Tests
```
