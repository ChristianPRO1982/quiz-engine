"""Sprint 6 tests for quiz preview mode."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

import quiz_engine.models  # noqa: F401
from quiz_engine.app import create_app
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.user import User
from quiz_engine.plugins.registry import build_default_registry
from quiz_engine.repositories.quiz_repository import QuizRepository
from quiz_engine.services.quiz_preview_service import QuizPreviewService


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "sprint6_preview.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())
    with get_session() as session:
        session.add_all([User(subject="user1"), User(subject="user2")])
        session.commit()


def test_preview_route_requires_authentication(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    response = client.get("/admin/quizzes/1/preview", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_preview_route_renders_for_authenticated_user(
    tmp_path: Path, monkeypatch
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "user1"})

    created = client.post("/admin/quizzes", follow_redirects=False)
    quiz_path = created.headers["location"]
    quiz_id = int(quiz_path.rsplit("/", 1)[-1])
    client.put(
        f"/api/quizzes/{quiz_id}",
        json={
            "schema_version": "v1",
            "title": "Sprint 6",
            "description": "Preview me",
            "questions": [
                {
                    "question_id": "slide-1",
                    "type": "slide",
                    "title": "Welcome",
                    "spec": {
                        "schema_version": "v0",
                        "type": "slide",
                        "content": {
                            "title": "Welcome",
                            "body": "Round starts now.",
                            "media": {"type": "none", "src": None},
                        },
                    },
                }
            ],
        },
    )

    response = client.get(f"/admin/quizzes/{quiz_id}/preview")

    assert response.status_code == 200
    assert "Read-only playtest using your current draft." in response.text
    assert "qe-preview-prev" in response.text
    assert "qe-preview-next" in response.text
    assert "qe-preview-bootstrap" in response.text


def test_preview_service_can_load_quiz_data(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    service = QuizPreviewService()
    repository = QuizRepository()

    with get_session() as session:
        user = session.query(User).filter_by(subject="user1").one()
        created = repository.create(
            session,
            schema_version="v1",
            payload={
                "schema_version": "v1",
                "title": "Owner quiz",
                "description": "",
                "questions": [],
            },
            created_by_user_id=user.id,
        )
        loaded = service.load_quiz(session, user_id=user.id, quiz_id=created.id)

    assert loaded.id == created.id
    assert loaded.payload["title"] == "Owner quiz"


def test_preview_service_iterates_all_stages_without_error() -> None:
    service = QuizPreviewService()
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(plugin_registry=build_default_registry())
        )
    )
    quiz = SimpleNamespace(
        id=77,
        schema_version="v1",
        payload={
            "schema_version": "v1",
            "title": "Preview quiz",
            "description": "",
            "questions": [
                {
                    "question_id": "slide-1",
                    "type": "slide",
                    "title": "Slide stage",
                    "spec": {
                        "schema_version": "v0",
                        "type": "slide",
                        "content": {"title": "Slide stage", "body": "Body"},
                    },
                },
                {
                    "question_id": "poll-1",
                    "type": "poll",
                    "title": "Poll stage",
                    "spec": {"options": ["A", "B"]},
                },
            ],
        },
    )

    preview = service.build_preview_payload(request, quiz=quiz)

    assert preview["quiz_id"] == 77
    assert len(preview["stages"]) == 2
    assert preview["stages"][0]["view_model"]["is_placeholder"] is False
    assert preview["stages"][1]["view_model"]["is_placeholder"] is True
