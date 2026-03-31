import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False) # producer/consumer/hybrid
    status: Mapped[str] = mapped_column(String(20), default="active")
    client_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    client_secret_enc: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    subscriber_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("subscribers.id"), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
