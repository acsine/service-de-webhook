import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.common.db import get_db
from app.common.redis import get_redis
from app.common.auth import get_current_user
from app.services.oauth.dependencies import get_producer_app
from app.models import Application, Event, Delivery
from app.services.events import services, schemas

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
async def publish_event(
    data: schemas.PublishEventRequest,
    background_tasks: BackgroundTasks,
    producer_app: Application = Depends(get_producer_app),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await services.publish_event(data, producer_app, db, redis, background_tasks)

@router.get("", response_model=List[Dict[str, Any]])
async def list_events(
    event_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    query = select(Event).where(Event.tenant_id == tenant_id)
    if event_type:
        query = query.where(Event.event_type == event_type)
    
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(Event.received_at.desc()).offset(offset).limit(limit))
    return [
        {
            "id": str(e.id), 
            "event_type": e.event_type, 
            "status": "processed" if e.processed_at else "pending", 
            "created_at": e.received_at
        } for e in result.scalars().all()
    ]

@router.get("/{id}")
async def get_event(
    id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    result = await db.execute(select(Event).where(Event.id == id, Event.tenant_id == tenant_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    del_result = await db.execute(select(Delivery).where(Delivery.event_id == id))
    deliveries = del_result.scalars().all()
    
    return {
        "id": str(event.id),
        "event_type": event.event_type,
        "payload": event.payload,
        "status": "processed" if event.processed_at else "pending",
        "created_at": event.received_at,
        "deliveries": [{"id": str(d.id), "subscriber_id": str(d.subscriber_id), "status": d.status} for d in deliveries]
    }
