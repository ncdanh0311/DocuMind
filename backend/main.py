from contextlib import asynccontextmanager
from pathlib import Path
import logging
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.db import engine
from backend.app.api import auth, documents, notebooks, notifications, jobs

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema changes belong to the explicit migration step, never API startup.
    yield

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"])

@app.exception_handler(Exception)
async def internal_error(request, exc):
    # Do not serialize provider/DB exceptions or credentials into logs or responses.
    logger.error("Unhandled API error (%s)", type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "ERR_INTERNAL_SERVER"})

@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    # Pydantic's default errors echo raw input, including submitted credentials.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]} for error in exc.errors()
    ]})

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API", "status": "online", "version": settings.VERSION}

@app.get("/health")
def health():
    return {"status": "online"}

@app.get("/ready")
def ready():
    try:
        config = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
        expected = set(ScriptDirectory.from_config(config).get_heads())
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            actual = set(MigrationContext.configure(connection).get_current_heads())
            vector = connection.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).scalar()
        if actual != expected or not vector:
            raise RuntimeError("Database not migrated")
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(notebooks.router, prefix=f"{settings.API_V1_STR}/notebooks", tags=["notebooks"])
app.include_router(documents.router, prefix=settings.API_V1_STR, tags=["documents"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])

app.include_router(jobs.router, prefix=settings.API_V1_STR, tags=["jobs"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
