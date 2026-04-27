import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter
from sqlalchemy import text

from sinc.config import get_settings
from sinc.db.session import AsyncSessionLocal

logger = structlog.get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["infra"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Verifica conectividade com Postgres e Redis. Sem autenticação."""
    status: dict[str, str] = {"postgres": "error", "redis": "error"}

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception:
        logger.warning("health.postgres_failed")

    try:
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        status["redis"] = "ok"
    except Exception:
        logger.warning("health.redis_failed")

    overall = "ok" if all(v == "ok" for v in status.values()) else "degraded"
    return {"status": overall, **status}
