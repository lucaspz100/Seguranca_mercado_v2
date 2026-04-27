from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def test_health_ok(client: AsyncClient) -> None:
    with (
        patch("sinc.api.routes.health.AsyncSessionLocal") as mock_session_cls,
        patch("sinc.api.routes.health.aioredis.from_url") as mock_redis_factory,
    ):
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock()
        mock_session_cls.return_value = mock_session

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.aclose = AsyncMock()
        mock_redis_factory.return_value = mock_redis

        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["postgres"] == "ok"
    assert data["redis"] == "ok"


async def test_health_degraded_redis(client: AsyncClient) -> None:
    with (
        patch("sinc.api.routes.health.AsyncSessionLocal") as mock_session_cls,
        patch("sinc.api.routes.health.aioredis.from_url") as mock_redis_factory,
    ):
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock()
        mock_session_cls.return_value = mock_session

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=ConnectionError("redis down"))
        mock_redis.aclose = AsyncMock()
        mock_redis_factory.return_value = mock_redis

        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["postgres"] == "ok"
    assert data["redis"] == "error"
