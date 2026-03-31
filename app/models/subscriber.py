import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, LargeBinary, Text, Integer, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    callback_url: Mapped[str] = mapped_column(Text, nullable=False)
    secret_hmac_enc: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    secret_hmac_key_id: Mapped[str] = mapped_column(String(50), nullable=False)
    events: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    max_retries: Mapped[int] = mapped_column(Integer, default=10)
    timeout_ms: Mapped[int] = mapped_column(Integer, default=5000)
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, default=1000)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_subscribers_events", "events", postgresql_using="gin"),
        Index("idx_subscribers_tenant_id", "tenant_id"),
    )
