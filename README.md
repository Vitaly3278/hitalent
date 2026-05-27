# Organizational Structure API

REST API for managing a company organizational structure: departments (tree) and employees.

## Stack

- **FastAPI** — HTTP API
- **SQLAlchemy** — ORM
- **PostgreSQL** — database
- **Alembic** — migrations
- **Docker Compose** — local run
- **pytest** — tests

## Project structure

```
hitalent/
├── app/
│   ├── main.py              # FastAPI app, exception handlers
│   ├── config.py            # Settings (env)
│   ├── database.py          # Engine & session
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic
│   └── api/routes/          # HTTP endpoints
├── alembic/                 # Migrations
├── tests/
├── docker-compose.yml
└── Dockerfile
```

## Quick start

```bash
docker compose up --build
```

API: http://localhost:8000  
OpenAPI docs: http://localhost:8000/docs  
Health: http://localhost:8000/health

Migrations run automatically on container start (`alembic upgrade head`).

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/departments/` | Create department |
| POST | `/departments/{id}/employees/` | Create employee |
| GET | `/departments/{id}` | Department details + tree (`depth`, `include_employees`) |
| PATCH | `/departments/{id}` | Update name and/or parent |
| DELETE | `/departments/{id}` | Delete (`mode=cascade` or `mode=reassign`) |

### Examples

Create root department:

```bash
curl -X POST http://localhost:8000/departments/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Company"}'
```

Get department with nested children (depth 3):

```bash
curl "http://localhost:8000/departments/1?depth=3&include_employees=true"
```

Delete with employee reassignment:

```bash
curl -X DELETE "http://localhost:8000/departments/2?mode=reassign&reassign_to_department_id=1"
```

## Local development (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hitalent
alembic upgrade head
uvicorn app.main:app --reload
```

## Tests

By default tests use in-memory SQLite (no extra setup):

```bash
pip install -r requirements.txt
pytest -v
```

To run tests against PostgreSQL:

```bash
docker compose up db -d
docker compose exec db psql -U postgres -c "CREATE DATABASE hitalent_test;"
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hitalent_test
pytest -v
```

## Business rules

- Department names are unique within the same parent
- Cannot set a department as its own parent or create cycles in the tree (409)
- Cascade delete removes child departments and employees at DB level
- Reassign delete moves employees to another department; child departments are reparented to the deleted department's parent
