import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from sinc.db.base import Base
from sinc.schemas.common import CameraLayer


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rtsp_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # TODO(KAN): confirmar modelo e posição exatos das câmeras Intelbras
    layer: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CameraLayer.SALON.value, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=text("NOW()")
    )
