import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from redis.asyncio import Redis
from app.models import Event, Application, AuditLog
from app.services.events.schemas import PublishEventRequest, EventResponse
from app.services.events.constants import IDEMPOTENCY_TTL, DEFAULT_RATE_LIMIT_PER_MIN
from app.common.queue import enqueue_job

async def publish_event(
    data: PublishEventRequest,
    producer_app: Application,
    db: AsyncSession,
    redis: Redis
) -> Dict[str, Any]:
    # 1. Tenant validation
    if str(producer_app.tenant_id) != data.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID mismatch")

    # 2. Idempotency Check
    if data.idempotency_key:
        cache_key = f"idempotency:{data.idempotency_key}"
        cached_id = await redis.get(cache_key)
        if cached_id:
            return {"event_id": cached_id, "status": "already_processed"}

    # 3. Rate Limit Check (Sliding Window 60s)
    rl_key = f"rl:producer:{producer_app.id}"
    count = await redis.incr(rl_key)
    if count == 1:
        await redis.expire(rl_key, 60)
    
    if count > DEFAULT_RATE_LIMIT_PER_MIN:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # 4. Persistence
    event = Event(
        tenant_id=producer_app.tenant_id,
        event_type=data.event_type,
        payload=data.payload,
        idempotency_key=data.idempotency_key,
        source_app=producer_app.client_id,
        target_app_id=data.target_app_id
    )

    db.add(event)
    await db.flush() # Get event.id

    # 5. Idempotency Save
    if data.idempotency_key:
        await redis.setex(f"idempotency:{data.idempotency_key}", IDEMPOTENCY_TTL, str(event.id))

    # 6. Enqueue
    await enqueue_job("dispatch_event", event_id=str(event.id))
    
    # 7. Audit Log
    audit = AuditLog(
        tenant_id=producer_app.tenant_id,
        actor=producer_app.client_id,
        action="event.published",
        resource_id=event.id
    )
    db.add(audit)
    
    await db.commit()
    
    return {"event_id": str(event.id), "status": "queued"}
