import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, LargeBinary, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from sinc.db.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Person(Base):
    """Entrada na watchlist. ADR-005: persistir apenas ~50 suspeitos conhecidos."""

    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("NOW()")
    )
    # TODO(KAN): definir responsável formal pela watchlist (ADR-002)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class PersonEmbedding(Base):
    """Embedding ArcFace de uma foto da watchlist. ADR-005: mínimo de dados."""

    __tablename__ = "person_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("persons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Embedding serializado como numpy array (float32, 512-dim para buffalo_l)
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    source_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("NOW()")
    )
