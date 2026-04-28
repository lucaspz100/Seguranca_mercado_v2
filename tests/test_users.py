"""Testes dos endpoints de gerenciamento de usuários."""

import uuid
from unittest.mock import patch

from httpx import AsyncClient
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from sinc.models.user import User
from sinc.schemas.common import Role

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ── helpers ────────────────────────────────────────────────────────────────


async def _make_user(
    db: AsyncSession,
    email: str,
    role: str = Role.OPERATOR.value,
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        username=email.split("@")[0],
        hashed_password=pwd_context.hash("senha123"),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _mock_redis(exists: bool = True):  # type: ignore[no-untyped-def]
    from unittest.mock import AsyncMock

    r = AsyncMock()
    r.setex = AsyncMock()
    r.exists = AsyncMock(return_value=1 if exists else 0)
    r.delete = AsyncMock()
    r.aclose = AsyncMock()
    return r


async def _login(client: AsyncClient, email: str) -> str:
    with patch("sinc.api.routes.auth._redis_client", return_value=_mock_redis()):
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "senha123"},
        )
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ── GET /api/v1/users ──────────────────────────────────────────────────────


async def test_list_users_as_admin(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        admin = await _make_user(db, "adm@sinc.local", Role.ADMIN.value)
        await _make_user(db, "op@sinc.local", Role.OPERATOR.value)

    token = await _login(client, "adm@sinc.local")
    resp = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    emails = {u["email"] for u in body["items"]}
    assert "adm@sinc.local" in emails
    assert "op@sinc.local" in emails


async def test_list_users_as_manager(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _make_user(db, "mgr@sinc.local", Role.MANAGER.value)

    token = await _login(client, "mgr@sinc.local")
    resp = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200


async def test_list_users_forbidden_for_operator(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _make_user(db, "oper@sinc.local", Role.OPERATOR.value)

    token = await _login(client, "oper@sinc.local")
    resp = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 403


# ── POST /api/v1/users ─────────────────────────────────────────────────────


async def test_create_user_as_admin(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _make_user(db, "adm2@sinc.local", Role.ADMIN.value)

    token = await _login(client, "adm2@sinc.local")
    resp = await client.post(
        "/api/v1/users",
        json={"email": "novo@example.com", "username": "novo", "password": "senha456"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "novo@example.com"
    assert body["role"] == Role.OPERATOR.value
    assert body["is_active"] is True


async def test_create_user_duplicate_email(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _make_user(db, "adm3@sinc.local", Role.ADMIN.value)
        await _make_user(db, "dup@example.com")

    token = await _login(client, "adm3@sinc.local")
    resp = await client.post(
        "/api/v1/users",
        json={"email": "dup@example.com", "username": "outro", "password": "senha456"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 409


async def test_create_user_forbidden_for_manager(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _make_user(db, "mgr2@sinc.local", Role.MANAGER.value)

    token = await _login(client, "mgr2@sinc.local")
    resp = await client.post(
        "/api/v1/users",
        json={"email": "x@sinc.local", "username": "x", "password": "senha456"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 403


# ── PATCH /api/v1/users/{id}/deactivate ────────────────────────────────────


async def test_deactivate_user(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        admin = await _make_user(db, "adm4@sinc.local", Role.ADMIN.value)
        target = await _make_user(db, "tgt@sinc.local")
        target_id = target.id

    token = await _login(client, "adm4@sinc.local")
    resp = await client.patch(
        f"/api/v1/users/{target_id}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


async def test_deactivate_self_forbidden(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        admin = await _make_user(db, "adm5@sinc.local", Role.ADMIN.value)
        admin_id = admin.id

    token = await _login(client, "adm5@sinc.local")
    resp = await client.patch(
        f"/api/v1/users/{admin_id}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 400


async def test_deactivate_already_inactive(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _make_user(db, "adm6@sinc.local", Role.ADMIN.value)
        inactive = await _make_user(db, "off@sinc.local", is_active=False)
        inactive_id = inactive.id

    token = await _login(client, "adm6@sinc.local")
    resp = await client.patch(
        f"/api/v1/users/{inactive_id}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 409


async def test_deactivate_not_found(client: AsyncClient, session_factory) -> None:  # type: ignore[no-untyped-def]
    async with session_factory() as db:
        await _make_user(db, "adm7@sinc.local", Role.ADMIN.value)

    token = await _login(client, "adm7@sinc.local")
    resp = await client.patch(
        f"/api/v1/users/{uuid.uuid4()}/deactivate",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 404
