# College Management API

FastAPI, SQLAlchemy 2.0, Pydantic v2, and SQLite. Requires Python 3.10+.
The project uses the existing workspace folder rather than creating a nested project.

## Run on Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs for Swagger UI. Stop with Ctrl+C.
If port 8000 is occupied, add `--port 8001` and use that port in the URLs.
SQLite tables are created at startup in `college.db` next to the source files.
An existing database is preserved; `create_all()` does not migrate changed schemas.

## Endpoints

| Method | Path | Result |
| --- | --- | --- |
| GET | `/` | API status message |
| GET | `/api/departments/` | Departments ordered by ID |
| POST | `/api/departments/` | Created department, HTTP 201 |
| GET | `/api/students/` | Students ordered by ID, including department names |
| POST | `/api/students/` | Created student, HTTP 201; missing department, HTTP 404 |

Names are trimmed and must contain 1-100 characters. Department IDs must be positive.
Invalid request bodies return HTTP 422. Department names are not required to be unique.

## Example Requests

With a fresh database, departments receive IDs 1 and 2. On subsequent runs, use
the IDs returned by the department creation responses.

```bash
curl -i -X POST http://127.0.0.1:8000/api/departments/ \
  -H 'Content-Type: application/json' -d '{"department_name":"Computer Science"}'
curl -i -X POST http://127.0.0.1:8000/api/departments/ \
  -H 'Content-Type: application/json' -d '{"department_name":"Mechanical Engineering"}'
curl -i -X POST http://127.0.0.1:8000/api/students/ \
  -H 'Content-Type: application/json' -d '{"student_name":"Asha Rao","department_id":1}'
curl -i -X POST http://127.0.0.1:8000/api/students/ \
  -H 'Content-Type: application/json' -d '{"student_name":"Rahul Mehta","department_id":2}'
curl -i http://127.0.0.1:8000/api/students/
curl -i -X POST http://127.0.0.1:8000/api/students/ \
  -H 'Content-Type: application/json' -d '{"student_name":"Ram","department_id":10}'
```

The last request returns `404` and `{"detail":"Department not found"}` provided
department 10 does not exist.

## Automated Validation

```bash
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest -v test_api
```

Tests use a separate in-memory database for each test, not `college.db`.
They cover documentation routes, OpenAPI methods and creation status codes,
empty lists, both example departments and students, populated department names,
the exact missing-department error, validation failures, SQLite foreign-key
enforcement, and database-session cleanup.

See [REVIEW.md](REVIEW.md) for the application line-by-line explanation,
supporting-file review, five required checks, and known limitations.
The latest Starlette installed during validation warns that its `httpx` test
client support is deprecated; the tests still pass. This affects tests, not API requests.

## Git

The virtual environments, bytecode, database, and SQLite sidecar files are ignored.
The intended commit message is `Scaffold College Management API with FastAPI`.
Git identity must already be configured; do not put credentials in the repository.