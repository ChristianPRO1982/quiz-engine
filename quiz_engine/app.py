"""FastAPI application for quiz-engine runtime."""

from __future__ import annotations

from typing import Any
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from auth.deps import get_current_user
from auth.settings import AuthSettings
from quiz_engine.db.session import get_session
from quiz_engine.i18n import get_translator, select_locale
from quiz_engine.middleware.session import SessionCookieMiddleware
from quiz_engine.plugins.registry import build_default_registry
from quiz_engine.routers.admin import router as admin_router
from quiz_engine.routers.auth import router as auth_router
from quiz_engine.routers.host import router as host_router
from quiz_engine.routers.join import router as join_router
from quiz_engine.routers.quiz_preview import router as quiz_preview_router
from quiz_engine.routers.quizzes import router as quizzes_router
from quiz_engine.routers.ws import router as ws_router
from quiz_engine.services.auth_service import list_user_roles_for_subject
from quiz_engine.services.session_live_service import SessionLiveService


def _template_auth_context(request: Request) -> dict[str, Any]:
    current_user = get_current_user(request)
    if current_user is None:
        return {"auth_roles": []}
    with get_session() as session:
        roles = list_user_roles_for_subject(session, subject=current_user.subject)
    return {"auth_roles": sorted(roles)}


def create_app() -> FastAPI:
    settings = AuthSettings.from_env()
    app = FastAPI()
    app.add_middleware(
        SessionCookieMiddleware,
        secret_key=settings.session_secret_key,
        cookie_name="qe_session",
    )

    templates_dir = Path(__file__).resolve().parent / "templates"
    static_dir = Path(__file__).resolve().parent / "static"
    templates = Jinja2Templates(
        directory=str(templates_dir),
        context_processors=[_template_auth_context],
    )
    app.state.templates = templates
    app.state.plugin_registry = build_default_registry()
    app.state.session_live_service = SessionLiveService()
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        locale = select_locale(request.headers.get("accept-language"))
        translator = get_translator(locale)
        return templates.TemplateResponse(
            request,
            "home.html",
            {
                "is_dev": settings.mode == "dev",
                "current_user": get_current_user(request),
                "locale": locale,
                "_": translator.gettext,
            },
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(quizzes_router)
    app.include_router(admin_router)
    app.include_router(quiz_preview_router)
    app.include_router(host_router)
    app.include_router(join_router)
    app.include_router(ws_router)

    return app


app = create_app()
