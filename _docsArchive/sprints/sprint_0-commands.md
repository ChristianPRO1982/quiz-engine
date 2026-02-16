# Sprint 0 Commands

## Docker Commands (Standard)
```
docker compose down --remove-orphans
docker compose up -d --build
docker compose logs -f quiz-engine
```
These commands stop containers, rebuild and start them in detached mode, then follow the logs.

## Docker Commands (Custom Ports)
```
TRAEFIK_HTTP_PORT=8081 TRAEFIK_HTTPS_PORT=8443 TRAEFIK_DASHBOARD_PORT=8082 docker compose up -d --build
```
Starts the application with custom Traefik ports to avoid conflicts with other services.

## Local Development (UV)
```
uv sync
uv run uvicorn quiz_engine.app:app --reload --proxy-headers
```
Syncs dependencies and runs the application locally with hot-reload enabled for development.

## Access URLs
- https://quiz-engine.localhost/ - Main application (via Traefik)
- http://127.0.0.1:8080 - Direct access to the application
