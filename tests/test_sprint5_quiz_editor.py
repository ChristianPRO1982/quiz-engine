"""Sprint 5 tests for quiz editor MVP."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import quiz_engine.models  # noqa: F401
from quiz_engine.app import create_app
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.user import User


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "sprint5_editor.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())
    with get_session() as session:
        session.add_all([User(subject="user1"), User(subject="user2")])
        session.commit()


def test_admin_create_quiz_redirects_to_editor(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "user1"})

    create = client.post("/admin/quizzes", follow_redirects=False)

    assert create.status_code == 303
    assert create.headers["location"].startswith("/admin/quizzes/")

    editor = client.get(create.headers["location"])
    assert editor.status_code == 200
    assert "Quiz editor" in editor.text
    assert "qe-editor-save" in editor.text


def test_admin_editor_routes_require_authentication(
    tmp_path: Path, monkeypatch
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    create = client.post("/admin/quizzes", follow_redirects=False)
    assert create.status_code == 303
    assert create.headers["location"] == "/login"

    detail = client.get("/admin/quizzes/1", follow_redirects=False)
    assert detail.status_code == 303
    assert detail.headers["location"] == "/login"


def test_editor_get_and_put_api_round_trip_with_ordering(
    tmp_path: Path, monkeypatch
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "user1"})

    created = client.post("/admin/quizzes", follow_redirects=False)
    quiz_path = created.headers["location"]
    quiz_id = int(quiz_path.rsplit("/", 1)[-1])

    initial = client.get(f"/api/quizzes/{quiz_id}")
    assert initial.status_code == 200
    assert initial.json()["quiz_id"] == quiz_id
    assert initial.json()["questions"] == []

    update_payload = {
        "schema_version": "v1",
        "title": "Sprint 5 Editor Quiz",
        "description": "manual save",
        "questions": [
            {
                "question_id": "q2",
                "type": "slide",
                "title": "Second",
                "spec": {"content": {"title": "Second", "body": "B"}},
            },
            {
                "question_id": "q1",
                "type": "slide",
                "title": "First",
                "spec": {"content": {"title": "First", "body": "A"}},
            },
        ],
    }
    saved = client.put(f"/api/quizzes/{quiz_id}", json=update_payload)

    assert saved.status_code == 200
    payload = saved.json()
    assert payload["title"] == "Sprint 5 Editor Quiz"
    assert [question["question_id"] for question in payload["questions"]] == [
        "q2",
        "q1",
    ]

    reloaded = client.get(f"/api/quizzes/{quiz_id}")
    assert reloaded.status_code == 200
    assert [question["question_id"] for question in reloaded.json()["questions"]] == [
        "q2",
        "q1",
    ]


def test_editor_get_normalizes_legacy_questions(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "user1"})

    created = client.post(
        "/api/quizzes",
        json={
            "schema_version": "v1",
            "title": "Legacy quiz",
            "description": "",
            "questions": [
                {
                    "type": "qcm_single",
                    "text": "Question text",
                    "choices": ["A", "B"],
                }
            ],
        },
    )
    quiz_id = created.json()["id"]

    detail = client.get(f"/api/quizzes/{quiz_id}")

    assert detail.status_code == 200
    data = detail.json()
    assert data["quiz_id"] == quiz_id
    assert data["questions"][0]["type"] == "qcm_single"
    assert data["questions"][0]["title"] == "Question text"
    assert data["questions"][0]["question_id"]


def test_editor_template_contains_required_controls(
    tmp_path: Path, monkeypatch
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "user1"})

    created = client.post("/admin/quizzes", follow_redirects=False)
    page = client.get(created.headers["location"])

    assert page.status_code == 200
    assert "qe-editor-status" in page.text
    assert "qe-editor-preview" in page.text
    assert "qe-editor-save" in page.text
    assert "qe-editor-add-question" in page.text
    assert "qe-question-type-modal" in page.text
    assert "qe-editor-delete-modal" in page.text
