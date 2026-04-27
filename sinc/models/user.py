import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from sinc.db.base import Base
from sinc.schemas.common import Role


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=Role.OPERATOR.value)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # TODO(KAN): 2FA obrigatório para MANAGER/ADMIN — aguardar definição de infra
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("NOW()")
    )
