"""Aplicação principal FastAPI."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import APP_TITLE, STATIC_DIR
from app.infrastructure.database import initialize_database
from app.presentation.routes_api import router as api_router
from app.presentation.routes_web import router as web_router

initialize_database()

app = FastAPI(title=APP_TITLE)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(web_router)
app.include_router(api_router)
