import uuid
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sinc.api.deps import get_current_user, oauth2_scheme
from sinc.config import get_settings
from sinc.db.session import get_db
from sinc.models.audit_log import AuditLog
from sinc.models.user import User
from sinc.schemas.auth import RefreshRequest, TokenPayload, TokenResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

_REDIS_KEY_PREFIX = "sinc:refresh:"


def _redis_client() -> aioredis.Redis:  # type: ignore[type-arg]
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def _make_token(user_id: str, token_type: str, expire_delta: timedelta) -> tuple[str, str]:
    """Retorna (token_str, jti)."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + expire_delta
    payload = {
        "sub": user_id,
        "jti": jti,
        "type": token_type,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti


async def _save_refresh_jti(r: aioredis.Redis, jti: str) -> None:  # type: ignore[type-arg]
    ttl = timedelta(days=settings.refresh_token_expire_days)
    await r.setex(_REDIS_KEY_PREFIX + jti, int(ttl.total_seconds()), "1")


async def _revoke_refresh_jti(r: aioredis.Redis, jti: str) -> None:  # type: ignore[type-arg]
    await r.delete(_REDIS_KEY_PREFIX + jti)


async def _decode_refresh_token(token: str) -> TokenPayload:
    try:
        raw = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        payload = TokenPayload(**raw)
        if payload.type != "refresh":
            raise ValueError("not a refresh token")
        return payload
    except (JWTError, Exception) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or not pwd_context.verify(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(user.id)
    access_token, _ = _make_token(
        user_id, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh_token, refresh_jti = _make_token(
        user_id, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )

    r = _redis_client()
    await _save_refresh_jti(r, refresh_jti)
    await r.aclose()

    ip = request.client.host if request.client else None
    db.add(AuditLog(user_id=user.id, action="auth.login", ip_address=ip))
    await db.commit()

    logger.info("auth.login", user_id=user_id, email=user.email)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest) -> TokenResponse:
    payload = await _decode_refresh_token(body.refresh_token)

    r = _redis_client()
    exists = await r.exists(_REDIS_KEY_PREFIX + payload.jti)
    if not exists:
        await r.aclose()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revogado")

    await _revoke_refresh_jti(r, payload.jti)

    access_token, _ = _make_token(
        payload.sub, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh_token, new_jti = _make_token(
        payload.sub, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )
    await _save_refresh_jti(r, new_jti)
    await r.aclose()

    logger.info("auth.refresh", user_id=payload.sub)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    payload = await _decode_refresh_token(body.refresh_token)

    r = _redis_client()
    await _revoke_refresh_jti(r, payload.jti)
    await r.aclose()

    ip = request.client.host if request.client else None
    db.add(AuditLog(user_id=current_user.id, action="auth.logout", ip_address=ip))
    await db.commit()

    logger.info("auth.logout", user_id=str(current_user.id))
