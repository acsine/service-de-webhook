import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class PublishEventRequest(BaseModel):
    event_type: str = Field(..., pattern=r"^[a-z_]+\.[a-z_]+$")
    tenant_id: str
    payload: Dict[str, Any]
    target_app_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    idempotency_key: Optional[str] = Field(None, max_length=255)

class EventResponse(BaseModel):
    event_id: uuid.UUID
    status: str
