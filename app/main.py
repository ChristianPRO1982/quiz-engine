from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.logging import configure_logging
from app.db.models import Base
from app.db.session import engine
from app.routers import health, quizzes, sessions, ws


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Quiz Engine")

    Base.metadata.create_all(bind=engine)

    app.include_router(health.router)
    app.include_router(quizzes.router)
    app.include_router(sessions.router)
    app.include_router(ws.router)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    templates = Jinja2Templates(directory="app/templates")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse("home.html", {"request": request})

    @app.get("/join/{session_code}", response_class=HTMLResponse)
    def join(request: Request, session_code: str):
        return templates.TemplateResponse(
            "join.html", {"request": request, "session_code": session_code}
        )

    @app.get("/host/{session_code}", response_class=HTMLResponse)
    def host(request: Request, session_code: str, token: str):
        return templates.TemplateResponse(
            "host.html",
            {"request": request, "session_code": session_code, "token": token},
        )

    @app.get("/play/{session_code}", response_class=HTMLResponse)
    def play(request: Request, session_code: str, player_id: int):
        return templates.TemplateResponse(
            "play.html",
            {"request": request, "session_code": session_code, "player_id": player_id},
        )

    @app.get("/review/{session_code}", response_class=HTMLResponse)
    def review(request: Request, session_code: str):
        return templates.TemplateResponse(
            "review.html", {"request": request, "session_code": session_code}
        )

    return app


app = create_app()
