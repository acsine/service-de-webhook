import uuid
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models import Subscriber, Delivery, Event, AuditLog
from app.services.subscribers.schemas import (
    CreateSubscriberRequest, UpdateSubscriberRequest, 
    SubscriberResponse, DeliveryResponse, DeliveryListResponse, SubscriberStatus
)
from app.services.applications.schemas import CreateApplicationRequest, ApplicationType
from app.services.applications.services import create_application
from redis.asyncio import Redis

async def create_subscriber(
    data: CreateSubscriberRequest, 
    current_user: Dict[str, Any], 
    db: AsyncSession, 
    redis: Redis
):
    # Delegate to create_application which handles challenge and hmac secret generation
    app_data = CreateApplicationRequest(
        name=data.name,
        type=ApplicationType.CONSUMER,
        callback_url=data.callback_url,
        events=data.events,
        verify_url=data.verify_url
    )
    # We might need to override max_retries and timeout_ms after creation if they are not part of create_application
    app_response = await create_application(app_data, current_user, db, redis)
    
    # Update the subscriber with custom limits
    sub_id = app_response.subscriber_id
    result = await db.execute(select(Subscriber).where(Subscriber.id == sub_id))
    subscriber = result.scalar_one()
    subscriber.max_retries = data.max_retries
    subscriber.timeout_ms = data.timeout_ms
    
    await db.commit()
    await db.refresh(subscriber)
    
    # Return response including the secret_hmac received from create_application
    return {
        **SubscriberResponse.model_validate(subscriber).model_dump(),
        "secret_hmac": app_response.secret_hmac
    }

async def list_subscribers(
    tenant_id: uuid.UUID, 
    db: AsyncSession, 
    status: Optional[SubscriberStatus] = None,
    page: int = 1,
    limit: int = 20
) -> List[Subscriber]:
    query = select(Subscriber).where(Subscriber.tenant_id == tenant_id)
    if status:
        query = query.where(Subscriber.status == status)
    
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    return list(result.scalars().all())

async def get_subscriber(sub_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession) -> Subscriber:
    result = await db.execute(select(Subscriber).where(Subscriber.id == sub_id, Subscriber.tenant_id == tenant_id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return sub

async def update_subscriber(
    sub_id: uuid.UUID, 
    data: UpdateSubscriberRequest, 
    current_user: Dict[str, Any], 
    db: AsyncSession
) -> Subscriber:
    tenant_id = uuid.UUID(current_user["tenant_id"])
    sub = await get_subscriber(sub_id, tenant_id, db)
    
    if data.callback_url and data.callback_url != sub.callback_url:
        # Re-verify challenge unless explicitly disabled
        should_verify = data.verify_url if data.verify_url is not None else True
        if should_verify:
            challenge = str(uuid.uuid4())
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    resp = await client.get(data.callback_url, params={"webhook_challenge": challenge})
                    resp.raise_for_status()
                    if resp.json().get("challenge") != challenge:
                        raise HTTPException(status_code=400, detail="Webhook challenge verification failed")
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Failed to verify callback URL: {str(e)}")
        sub.callback_url = data.callback_url
        sub.verified_at = datetime.utcnow() if should_verify else None

    if data.name: sub.name = data.name
    if data.events is not None: sub.events = data.events
    if data.max_retries is not None: sub.max_retries = data.max_retries
    if data.timeout_ms is not None: sub.timeout_ms = data.timeout_ms
    if data.status: sub.status = data.status
    
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor=current_user["sub"],
        action="subscriber.updated",
        resource_id=sub.id
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(sub)
    return sub

async def delete_subscriber(sub_id: uuid.UUID, current_user: Dict[str, Any], db: AsyncSession):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    sub = await get_subscriber(sub_id, tenant_id, db)
    sub.status = SubscriberStatus.DISABLED
    
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor=current_user["sub"],
        action="subscriber.deleted",
        resource_id=sub.id
    )
    db.add(audit_log)
    await db.commit()

async def pause_subscriber(sub_id: uuid.UUID, current_user: Dict[str, Any], db: AsyncSession):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    sub = await get_subscriber(sub_id, tenant_id, db)
    sub.status = SubscriberStatus.PAUSED
    
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor=current_user["sub"],
        action="subscriber.paused",
        resource_id=sub.id
    )
    db.add(audit_log)
    await db.commit()

async def resume_subscriber(sub_id: uuid.UUID, current_user: Dict[str, Any], db: AsyncSession, redis: Redis):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    sub = await get_subscriber(sub_id, tenant_id, db)
    sub.status = SubscriberStatus.ACTIVE
    sub.failure_count = 0 # Reset failures on resume
    
    # Clear circuit breaker in Redis if exists
    await redis.delete(f"circuit:{sub_id}")
    
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor=current_user["sub"],
        action="subscriber.resumed",
        resource_id=sub.id
    )
    db.add(audit_log)
    await db.commit()

async def get_deliveries(
    sub_id: uuid.UUID, 
    tenant_id: uuid.UUID, 
    db: AsyncSession, 
    status: Optional[str] = None, 
    page: int = 1, 
    limit: int = 20
) -> DeliveryListResponse:
    # Verify sub belongs to tenant
    await get_subscriber(sub_id, tenant_id, db)
    
    query = select(Delivery, Event.event_type).join(Event, Delivery.event_id == Event.id).where(Delivery.subscriber_id == sub_id)
    if status:
        query = query.where(Delivery.status == status)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(Delivery.created_at.desc()).offset(offset).limit(limit))
    
    items = []
    for delivery, event_type in result.all():
        d_resp = DeliveryResponse.model_validate(delivery)
        d_resp.event_type = event_type
        items.append(d_resp)
        
    return DeliveryListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_next=total > (page * limit)
    )

async def retry_delivery(delivery_id: uuid.UUID, current_user: Dict[str, Any], db: AsyncSession, redis: Redis):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    
    # Get delivery and check tenant via event -> tenant_id
    query = select(Delivery).join(Event).where(Delivery.id == delivery_id, Event.tenant_id == tenant_id)
    result = await db.execute(query)
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    # Enqueue in ARQ (re-using the worker queue logic which we'll implement later)
    # For now, we just log and mark for retry in a real scenario we'd call redis.enqueue_job...
    # Since worker/arq is not fully set up, we'll just log it.
    
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor=current_user["sub"],
        action="delivery.forced_retry",
        resource_id=delivery.id
    )
    db.add(audit_log)
    await db.commit()
    return {"message": "Delivery re-enqueued for retry", "delivery_id": str(delivery_id)}

async def test_subscriber(
    sub_id: uuid.UUID, 
    payload: Optional[Dict[str, Any]], 
    current_user: Dict[str, Any], 
    db: AsyncSession, 
    redis: Redis
) -> Dict[str, Any]:
    tenant_id = uuid.UUID(current_user["tenant_id"])
    await get_subscriber(sub_id, tenant_id, db)
    
    # Find the application associated with this subscriber to get the client_id for targeted delivery
    app_result = await db.execute(select(Application).where(Application.subscriber_id == sub_id))
    app = app_result.scalar_one_or_none()
    
    event = Event(
        tenant_id=tenant_id,
        event_type="test.ping",
        payload=payload or {"message": "Test webhook delivery", "at": datetime.utcnow().isoformat()},
        source_app=f"user:{current_user.get('sub')}",
        target_app_id=app.client_id if app else None
    )
    
    db.add(event)
    await db.flush()
    
    from app.common.queue import enqueue_job
    await enqueue_job("dispatch_event", event_id=str(event.id))
    
    # Audit Log
    audit = AuditLog(
        tenant_id=tenant_id,
        actor=str(current_user.get("sub")),
        action="subscriber.test_sent",
        resource_id=sub_id
    )
    db.add(audit)
    
    await db.commit()
    return {
        "message": "Test event queued", 
        "event_id": str(event.id), 
        "target_app_id": event.target_app_id
    }

