from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sinc.api.routes import auth, health
from sinc.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("sinc.startup", environment=settings.environment)
    yield
    logger.info("sinc.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SINC API",
        description="Sistema Inteligente de Notificação e Captura — Supermercado Kan",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "prod" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # TODO(KAN): restringir para domínio real
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")

    return app


app = create_app()
