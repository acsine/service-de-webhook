import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class SubscriberStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"

class CreateSubscriberRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    callback_url: str = Field(..., pattern=r"^https://")
    events: List[str]
    max_retries: int = Field(10, ge=1, le=20)
    timeout_ms: int = Field(5000, ge=1000, le=30000)
    verify_url: bool = True

class UpdateSubscriberRequest(BaseModel):
    name: Optional[str] = None
    callback_url: Optional[str] = Field(None, pattern=r"^https://")
    events: Optional[List[str]] = None
    max_retries: Optional[int] = Field(None, ge=1, le=20)
    timeout_ms: Optional[int] = Field(None, ge=1000, le=30000)
    status: Optional[SubscriberStatus] = None
    verify_url: Optional[bool] = None

class SubscriberResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    callback_url: str
    events: List[str]
    status: SubscriberStatus
    max_retries: int
    timeout_ms: int
    rate_limit_per_min: int
    failure_count: int
    last_failure_at: Optional[datetime]
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DeliveryResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    event_type: str
    status: str
    http_status: Optional[int]
    attempt_number: int
    duration_ms: Optional[int]
    delivered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class DeliveryListResponse(BaseModel):
    items: List[DeliveryResponse]
    total: int
    page: int
    limit: int
    has_next: bool
