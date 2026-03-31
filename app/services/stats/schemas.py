from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class Period(str, Enum):
    P1H = "1h"
    P24H = "24h"
    P7D = "7d"
    P30D = "30d"

class Granularity(str, Enum):
    HOUR = "hour"
    DAY = "day"

class OverviewResponse(BaseModel):
    total_events: int
    success_rate: float
    p95_latency_ms: float
    pending_count: int
    period: Period

class EventsByTypeItem(BaseModel):
    event_type: str
    count: int
    date: str

class DeliveryRateItem(BaseModel):
    timestamp: str
    success_count: int
    failure_count: int
    success_rate: float

class LatencyItem(BaseModel):
    timestamp: str
    avg_ms: float
    p95_ms: float
    p99_ms: float

class RetryItem(BaseModel):
    subscriber_id: str
    name: str
    retry_count: int
    circuit_breaker_status: str

class TopSubscriberItem(BaseModel):
    subscriber_id: str
    name: str
    delivery_count: int
    success_rate: float
