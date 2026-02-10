"""FastAPI application for quiz-engine runtime."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from auth.deps import get_current_user
from auth.settings import AuthSettings
from quiz_engine.i18n import get_translator, select_locale
from quiz_engine.middleware.session import SessionCookieMiddleware
from quiz_engine.routers.admin import router as admin_router
from quiz_engine.routers.auth import router as auth_router
from quiz_engine.routers.quizzes import router as quizzes_router


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
    templates = Jinja2Templates(directory=str(templates_dir))
    app.state.templates = templates
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

    return app


app = create_app()
