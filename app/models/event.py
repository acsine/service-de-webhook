import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    source_app: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_app_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    received_at: Mapped[datetime] = mapped_column(server_default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    __table_args__ = (
        Index("idx_events_tenant_type", "tenant_id", "event_type"),
        Index("idx_events_received_at", received_at.desc()),
    )
