from contextlib import asynccontextmanager
from pathlib import Path
import logging
import time
import uuid
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.core.db import engine
from backend.app.api import auth, documents, notebooks, notifications, jobs, reading

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema changes belong to the explicit migration step, never API startup.
    yield

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

@app.middleware("http")
async def request_logging(request, call_next):
    request_id = uuid.uuid4().hex
    started = time.monotonic()
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    # Log the route template only: paths, query strings and headers may contain personal data.
    route = getattr(request.scope.get("route"), "path", "unmatched")
    logger.info("request_id=%s method=%s route=%s status=%s code=%s duration_ms=%d", request_id,
                request.method, route, response.status_code, getattr(request.state, "error_code", "-"),
                (time.monotonic() - started) * 1000)
    return response
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_credentials=False, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"], expose_headers=["X-Request-ID"])

@app.exception_handler(StarletteHTTPException)
async def coded_http_error(request, exc):
    if isinstance(exc.detail, str) and exc.detail.startswith("ERR_"):
        request.state.error_code = exc.detail
    return await http_exception_handler(request, exc)

@app.exception_handler(Exception)
async def internal_error(request, exc):
    # Do not serialize provider/DB exceptions or credentials into logs or responses.
    request_id = getattr(request.state, "request_id", uuid.uuid4().hex)
    logger.error("request_id=%s code=ERR_INTERNAL_SERVER exception_type=%s", request_id, type(exc).__name__)
    return JSONResponse(status_code=500, content={"detail": "ERR_INTERNAL_SERVER"}, headers={"X-Request-ID": request_id})

@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    request.state.error_code = "ERR_VALIDATION"
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
app.include_router(reading.router, prefix=settings.API_V1_STR, tags=["reading"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
