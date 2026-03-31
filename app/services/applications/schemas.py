import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field

class ApplicationType(str, Enum):
    PRODUCER = "producer"
    CONSUMER = "consumer"
    HYBRID = "hybrid"

class CreateApplicationRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    type: ApplicationType
    callback_url: Optional[str] = None
    events: Optional[List[str]] = None
    verify_url: bool = True

class UpdateApplicationRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    type: ApplicationType
    status: str
    client_id: Optional[str] = None
    subscriber_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationCreatedResponse(ApplicationResponse):
    client_secret: Optional[str] = None
    secret_hmac: Optional[str] = None
