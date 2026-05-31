from fastapi import FastAPI

from app.database import init_db
from routers.health import router as health_router
from routers.report import router as report_router
from routers.line import router as line_router
from routers.reports import router as reports_router
from routers.chat import router as chat_router
from routers.webhook import router as webhook_router
from routers.sessions import router as sessions_router


app = FastAPI(
    title="Disaster Report API",
    description="A production-ready FastAPI service for ingesting disaster reports via LINE, chat, and Web APIs.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(health_router)
app.include_router(report_router)
app.include_router(line_router)
app.include_router(chat_router)
app.include_router(webhook_router)
app.include_router(sessions_router)
app.include_router(reports_router)

