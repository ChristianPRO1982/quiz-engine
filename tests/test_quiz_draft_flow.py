"""Sprint 3 tests for session-backed quiz draft flow."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

import quiz_engine.models  # noqa: F401
from quiz_engine.app import create_app
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.quiz import Quiz
from quiz_engine.models.user import User
from quiz_engine.schemas.quiz_schemas import QuizCreateRequest


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "sprint3_draft.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())
    with get_session() as session:
        session.add_all([User(subject="user1"), User(subject="user2")])
        session.commit()


def test_guided_draft_flow_create_quiz_and_redirect_to_detail(
    tmp_path: Path, monkeypatch
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "user1"})

    page = client.get("/admin/quizzes/new/step-1")
    assert page.status_code == 200
    assert "Step 1/3" in page.text

    step1 = client.post(
        "/admin/quizzes/new/step-1",
        data={"title": "Sprint 3 Quiz", "description": "Guided flow"},
        follow_redirects=False,
    )
    assert step1.status_code == 303
    assert step1.headers["location"] == "/admin/quizzes/new/step-2"

    step2_first_load = client.get("/admin/quizzes/new/step-2")
    assert step2_first_load.status_code == 200
    assert "Add questions" in step2_first_load.text

    step2_add = client.post(
        "/admin/quizzes/new/step-2",
        data={
            "action": "add",
            "question": "What is 2+2?",
            "choice1": "3",
            "choice2": "4",
            "choice3": "5",
        },
        follow_redirects=False,
    )
    assert step2_add.status_code == 303
    assert step2_add.headers["location"] == "/admin/quizzes/new/step-2"

    step2_refresh = client.get("/admin/quizzes/new/step-2")
    assert "What is 2+2?" in step2_refresh.text

    review_redirect = client.post(
        "/admin/quizzes/new/step-2",
        data={"action": "review"},
        follow_redirects=False,
    )
    assert review_redirect.status_code == 303
    assert review_redirect.headers["location"] == "/admin/quizzes/new/review"

    review = client.get("/admin/quizzes/new/review")
    assert review.status_code == 200
    assert "Sprint 3 Quiz" in review.text
    assert "What is 2+2?" in review.text

    save = client.post("/admin/quizzes/new/save", follow_redirects=False)
    assert save.status_code == 303
    assert save.headers["location"].startswith("/admin/quizzes/")

    detail = client.get(save.headers["location"])
    assert detail.status_code == 200
    assert "Sprint 3 Quiz" in detail.text
    assert "What is 2+2?" in detail.text

    listing = client.get("/admin/quizzes")
    assert listing.status_code == 200
    assert "Sprint 3 Quiz" in listing.text


def test_draft_save_fails_without_questions(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "user1"})
    client.post(
        "/admin/quizzes/new/step-1",
        data={"title": "No question quiz", "description": ""},
    )

    review = client.get("/admin/quizzes/new/review")
    assert review.status_code == 200

    save = client.post("/admin/quizzes/new/save")
    assert save.status_code == 400
    assert "at least" in save.text.lower() or "validation" in save.text.lower()


def test_admin_new_legacy_submit_paths(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "user1"})

    invalid = client.post(
        "/admin/quizzes/new",
        data={
            "title": "",
            "description": "desc",
            "question": "",
            "choice1": "",
            "choice2": "",
            "choice3": "",
        },
    )
    assert invalid.status_code == 400
    assert "Title is required." in invalid.text

    created = client.post(
        "/admin/quizzes/new",
        data={
            "title": "Legacy Quiz",
            "description": "legacy flow",
            "question": "Legacy question?",
            "choice1": "A",
            "choice2": "B",
            "choice3": "C",
        },
        follow_redirects=False,
    )
    assert created.status_code == 303
    assert created.headers["location"].startswith("/admin/quizzes/")

    detail = client.get(created.headers["location"])
    assert detail.status_code == 200
    assert "Legacy Quiz" in detail.text


def test_admin_step2_and_save_validation_branches(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "user1"})

    client.post(
        "/admin/quizzes/new/step-1",
        data={"title": "Validation Quiz", "description": ""},
    )

    back = client.post(
        "/admin/quizzes/new/step-2",
        data={"action": "back"},
        follow_redirects=False,
    )
    assert back.status_code == 303
    assert back.headers["location"] == "/admin/quizzes/new/step-1"

    no_text = client.post(
        "/admin/quizzes/new/step-2",
        data={"action": "add", "question": "", "choice1": "A", "choice2": "B"},
    )
    assert no_text.status_code == 400
    assert "Question text is required." in no_text.text

    not_enough_choices = client.post(
        "/admin/quizzes/new/step-2",
        data={"action": "add", "question": "Q?", "choice1": "A", "choice2": ""},
    )
    assert not_enough_choices.status_code == 400
    assert "At least two non-empty choices are required." in not_enough_choices.text

    next_review = client.post(
        "/admin/quizzes/new/step-2",
        data={
            "action": "add",
            "question": "Q2?",
            "choice1": "A",
            "choice2": "B",
            "next": "review",
        },
        follow_redirects=False,
    )
    assert next_review.status_code == 303
    assert next_review.headers["location"] == "/admin/quizzes/new/review"

    from quiz_engine.routers import admin as admin_router

    original = admin_router.draft_service.build_create_request

    def _raise_validation(request):  # noqa: ANN001
        try:
            QuizCreateRequest(schema_version="v1", title="", questions=[])
        except Exception as exc:  # noqa: BLE001
            raise exc
        raise AssertionError("Expected validation error")

    admin_router.draft_service.build_create_request = _raise_validation
    try:
        save = client.post("/admin/quizzes/new/save")
    finally:
        admin_router.draft_service.build_create_request = original

    assert save.status_code == 400
    assert "validation error" in save.text.lower()


def test_admin_routes_redirect_when_anonymous(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    get_paths = [
        "/admin/quizzes/new",
        "/admin/quizzes/new/step-1",
        "/admin/quizzes/new/step-2",
        "/admin/quizzes/new/review",
        "/admin/quizzes/1",
    ]
    for path in get_paths:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    post_paths = [
        "/admin/quizzes/new",
        "/admin/quizzes/new/step-1",
        "/admin/quizzes/new/step-2",
        "/admin/quizzes/new/save",
        "/admin/quizzes/1/duplicate",
    ]
    for path in post_paths:
        response = client.post(path, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"


def test_admin_detail_duplicate_and_error_paths(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "user1"})

    created = client.post(
        "/api/quizzes",
        json={
            "schema_version": "v1",
            "title": "Payload Quiz",
            "description": "payload branch",
            "questions": [
                {
                    "type": "qcm_single",
                    "text": "Good?",
                    "choices": ["A", "B"],
                }
            ],
        },
    )
    quiz_id = created.json()["id"]

    with get_session() as session:
        quiz = session.get(Quiz, quiz_id)
        assert quiz is not None
        quiz.payload = {
            "title": "Payload Quiz",
            "description": "payload",
            "questions": "x",
        }
        session.add(quiz)
        session.commit()

    detail = client.get(f"/admin/quizzes/{quiz_id}")
    assert detail.status_code == 200
    assert "No questions in this quiz." in detail.text

    with get_session() as session:
        quiz = session.get(Quiz, quiz_id)
        assert quiz is not None
        quiz.payload = []
        session.add(quiz)
        session.commit()

    duplicate = client.post(
        f"/admin/quizzes/{quiz_id}/duplicate",
        follow_redirects=False,
    )
    assert duplicate.status_code == 303
    assert duplicate.headers["location"] == "/admin/quizzes/new/step-1"

    from quiz_engine.routers import admin as admin_router

    original = admin_router.quiz_service.get_quiz_detail

    def _boom(*args, **kwargs):  # noqa: ANN002, ANN003
        raise HTTPException(status_code=500, detail="forced")

    admin_router.quiz_service.get_quiz_detail = _boom
    try:
        response = client.get(f"/admin/quizzes/{quiz_id}")
        assert response.status_code == 500
    finally:
        admin_router.quiz_service.get_quiz_detail = original
