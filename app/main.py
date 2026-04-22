from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.pages import router as pages_router
from app.api.submissions import router as submissions_router
from app.core.config import settings
from app.core.database import check_db_connection


@asynccontextmanager
async def lifespan(_: FastAPI):
    check_db_connection()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_router)
app.include_router(pages_router)
app.include_router(submissions_router)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
def healthcheck_db() -> dict[str, str]:
    try:
        check_db_connection()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc
    return {"status": "ok"}
