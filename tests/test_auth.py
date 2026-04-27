"""Testes de autenticação. Redis mockado; banco usa SQLite in-memory via conftest."""

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from sinc.models.user import User
from sinc.schemas.common import Role

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ── helpers ────────────────────────────────────────────────────────────────


async def _create_user(
    db: AsyncSession,
    email: str = "op@sinc.local",
    role: str = Role.OPERATOR.value,
) -> User:
    user = User(
        email=email,
        username=email.split("@")[0],
        hashed_password=pwd_context.hash("senha123"),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _mock_redis(exists: bool = True) -> MagicMock:
    r = AsyncMock()
    r.setex = AsyncMock()
    r.exists = AsyncMock(return_value=1 if exists else 0)
    r.delete = AsyncMock()
    r.aclose = AsyncMock()
    return r


# ── login ──────────────────────────────────────────────────────────────────


async def test_login_success(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _create_user(db)

    with patch("sinc.api.routes.auth._redis_client", return_value=_mock_redis()):
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "op@sinc.local", "password": "senha123"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _create_user(db, email="op2@sinc.local")

    with patch("sinc.api.routes.auth._redis_client", return_value=_mock_redis()):
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "op2@sinc.local", "password": "errada"},
        )

    assert resp.status_code == 401


async def test_login_unknown_email(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "nao@existe.com", "password": "qualquer"},
    )
    assert resp.status_code == 401


# ── refresh ────────────────────────────────────────────────────────────────


async def test_refresh_valid(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _create_user(db, email="rf@sinc.local")

    with patch("sinc.api.routes.auth._redis_client", return_value=_mock_redis(exists=True)):
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "rf@sinc.local", "password": "senha123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_revoked(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _create_user(db, email="rv@sinc.local")

    with patch("sinc.api.routes.auth._redis_client", return_value=_mock_redis(exists=True)):
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "rv@sinc.local", "password": "senha123"},
        )
        refresh_token = login_resp.json()["refresh_token"]

    with patch("sinc.api.routes.auth._redis_client", return_value=_mock_redis(exists=False)):
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert resp.status_code == 401


# ── logout ─────────────────────────────────────────────────────────────────


async def test_logout(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _create_user(db, email="lo@sinc.local")

    with patch("sinc.api.routes.auth._redis_client", return_value=_mock_redis(exists=True)):
        login_resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "lo@sinc.local", "password": "senha123"},
        )
        access_token = login_resp.json()["access_token"]
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 204

    with patch("sinc.api.routes.auth._redis_client", return_value=_mock_redis(exists=False)):
        resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert resp2.status_code == 401
