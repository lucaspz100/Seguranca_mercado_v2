import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from sinc.db.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """Log de auditoria append-only. ADR-005 + princípio de auditabilidade total.

    NUNCA emitir UPDATE ou DELETE nesta tabela — nenhum método deve ser exposto.
    Em produção, reforçar via Row-Level Security no Postgres.
    """

    __tablename__ = "audit_log"

    # BigInteger para Postgres (BIGSERIAL); com_variant para SQLite que só suporta INTEGER como rowid
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"), primary_key=True, autoincrement=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # JSON portável: mapeado para JSONB no Postgres via migration DDL explícita
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # INET armazenado como VARCHAR no ORM; migration usa tipo INET nativo
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("NOW()"), index=True
    )
