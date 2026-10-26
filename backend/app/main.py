from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import SessionLocal
from app.routers import (
    admin_courses,
    admin_editorial,
    admin_operations,
    auth,
    public,
    student,
)
from app.services.content_service import publicar_agendados

logging.basicConfig(
    level=logging.INFO if not settings.is_production else logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("clop")

UPLOAD_ROOT = Path(settings.UPLOAD_DIR)
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
(UPLOAD_ROOT / "comprovativos").mkdir(parents=True, exist_ok=True)


def _publicar_agendados() -> None:
    db = SessionLocal()
    try:
        publicados = publicar_agendados(db)
        if publicados:
            logger.info("Artigos agendados publicados: %s", publicados)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _publicar_agendados()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(public.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(student.router, prefix=settings.API_PREFIX)
app.include_router(admin_courses.router, prefix=settings.API_PREFIX)
app.include_router(admin_editorial.router, prefix=settings.API_PREFIX)
app.include_router(admin_operations.router, prefix=settings.API_PREFIX)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    problemas = []
    for erro in exc.errors():
        local = ".".join(str(p) for p in erro.get("loc", []) if p != "body")
        problemas.append(f"{local}: {erro.get('msg')}" if local else str(erro.get("msg")))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": problemas or ["Dados inválidos."]},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Ocorreu um erro interno. Tente novamente mais tarde."},
    )


@app.get("/", tags=["Root"])
def root() -> dict:
    return {
        "nome": settings.PROJECT_NAME,
        "descricao": settings.PROJECT_DESCRIPTION,
        "versao": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
    }


@app.get(f"{settings.API_PREFIX}/health", tags=["Health"])
def health() -> dict:
    return {"status": "ok", "versao": settings.VERSION}
