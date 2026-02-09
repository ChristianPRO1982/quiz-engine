# quiz-engine

[![Latest Release](https://img.shields.io/github/release/ChristianPRO1982/quiz-engine.svg?style=for-the-badge)](https://github.com/ChristianPRO1982/quiz-engine/releases/latest)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI/CD-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=for-the-badge)

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![WebSocket](https://img.shields.io/badge/WebSocket-real--time-ff9800?style=for-the-badge)

![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/docker--compose-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)


🇬🇧 EN:  Lightweight FastAPI-based quiz engine with REST APIs and WebSockets for running live quiz sessions on smartphones.

🇫🇷 FR: Moteur de quiz temps réel basé sur FastAPI, utilisant des API REST et WebSockets pour des sessions live sur smartphones.

## General architecture for quiz-engine (FastAPI + REST + WebSocket + PostgreSQL)

```mermaid
flowchart TB

  subgraph Clients[Clients]
    H[Host mobile-desktop Browser]
    P[Players smartphones Browser]
  end

  subgraph App[quiz-engine - FastAPI]
    REST[REST API - create/list quiz - start session - join session - read results]
    WS[WebSocket Gateway - live events - answers - stats]
    LIVE[In-memory Live State - connected players - current question - live counts]
    TPL[Jinja2 Templates mobile-first UI]
    SVC[Services Layer business logic]
    REPO[Repositories SQLAlchemy 2.0]
  end

  subgraph Data[Persistence]
    DB[PostgreSQL quizzes, sessions, players, answers]
    MIG[Alembic migrations]
  end

  H -->|HTTP| TPL
  P -->|HTTP| TPL

  H -->|REST| REST
  P -->|REST| REST

  H <-->|WebSocket| WS
  P <-->|WebSocket| WS

  REST --> SVC
  WS --> SVC
  SVC <--> LIVE

  SVC --> REPO
  REPO --> DB
  MIG --> DB

```

## Database migrations (Alembic)

- `DATABASE_URL` is required and must point to the shared PostgreSQL database.
- Only `qe_*` tables (plus `qe_alembic_version`) are managed by this service.

Create a migration:

```bash
uv run alembic revision --autogenerate -m "create qe_* core tables"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Rollback one migration:

```bash
uv run alembic downgrade -1
```

## i18n (gettext)

- Sources live in `quiz_engine/i18n/locales/*/LC_MESSAGES/messages.po`.
- Consent texts use versioned keys like `consent.pseudo.v1.body`.

Extract and update catalogs:

```bash
uv run pybabel extract -F babel.cfg -k _ -k t -o quiz_engine/i18n/locales/messages.pot .
uv run pybabel update -i quiz_engine/i18n/locales/messages.pot -d quiz_engine/i18n/locales -l en -l fr
```

Compile catalogs:

```bash
uv run pybabel compile -d quiz_engine/i18n/locales
```
