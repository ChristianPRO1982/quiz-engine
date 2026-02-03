"""FastAPI application for quiz-engine runtime."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from auth.settings import AuthSettings
from quiz_engine.i18n import get_translator, select_locale


def create_app() -> FastAPI:
    app = FastAPI()

    templates_dir = Path(__file__).resolve().parent / "templates"
    static_dir = Path(__file__).resolve().parent / "static"
    templates = Jinja2Templates(directory=str(templates_dir))
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        settings = AuthSettings.from_env()
        locale = select_locale(request.headers.get("accept-language"))
        translator = get_translator(locale)
        return templates.TemplateResponse(
            request,
            "home.html",
            {"is_dev": settings.mode == "dev", "_": translator.gettext},
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
