# HTTP Endpoints V0 (quiz-engine only)

Status: DRAFT

## GET /health
Lightweight health check for the service.

Response (200):
```
{
  "status": "ok"
}
```

Invariants:
- Response is JSON-only.
- No extra fields.
