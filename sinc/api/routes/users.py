import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sinc.api.deps import get_db, get_current_user, require_role
from sinc.models.audit_log import AuditLog
from sinc.models.user import User
from sinc.schemas.common import Role
from sinc.schemas.users import UserCreate, UserListResponse, UserResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@router.get("", response_model=UserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    _current: User = Depends(require_role(Role.MANAGER, Role.ADMIN)),
) -> UserListResponse:
    """Lista todos os usuários. Requer MANAGER ou ADMIN."""
    result = await db.execute(select(User).order_by(User.created_at))
    users = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar_one()
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_role(Role.ADMIN)),
) -> UserResponse:
    """Cria novo usuário. Apenas ADMIN pode criar usuários com qualquer papel."""
    existing = await db.execute(
        select(User).where((User.email == body.email) | (User.username == body.username))
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email ou username já em uso",
        )

    user = User(
        email=body.email,
        username=body.username,
        hashed_password=pwd_context.hash(body.password),
        role=body.role.value,
    )
    db.add(user)
    await db.flush()

    db.add(
        AuditLog(
            user_id=current.id,
            action="user.created",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": body.email, "username": body.username, "role": body.role.value},
        )
    )
    await db.commit()
    await db.refresh(user)

    logger.info("user.created", created_by=str(current.id), new_user=str(user.id), role=body.role.value)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_role(Role.ADMIN)),
) -> UserResponse:
    """Desativa um usuário. Apenas ADMIN. Não é possível desativar a si mesmo."""
    if user_id == current.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível desativar a própria conta",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Usuário já está inativo"
        )

    user.is_active = False
    db.add(
        AuditLog(
            user_id=current.id,
            action="user.deactivated",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email},
        )
    )
    await db.commit()
    await db.refresh(user)

    logger.info("user.deactivated", deactivated_by=str(current.id), target_user=str(user.id))
    return UserResponse.model_validate(user)
