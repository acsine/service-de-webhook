import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.common.db import get_db
from app.common.redis import get_redis
from app.common.auth import get_current_user
from app.services.subscribers import services, schemas

router = APIRouter(prefix="/subscribers", tags=["Subscribers"])

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_subscriber(
    data: schemas.CreateSubscriberRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await services.create_subscriber(data, current_user, db, redis)

@router.get("", response_model=List[schemas.SubscriberResponse])
async def list_subscribers(
    status: Optional[schemas.SubscriberStatus] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await services.list_subscribers(tenant_id, db, status, page, limit)

@router.get("/{id}", response_model=schemas.SubscriberResponse)
async def get_subscriber(
    id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await services.get_subscriber(id, tenant_id, db)

@router.patch("/{id}", response_model=schemas.SubscriberResponse)
async def update_subscriber(
    id: uuid.UUID,
    data: schemas.UpdateSubscriberRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await services.update_subscriber(id, data, current_user, db)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscriber(
    id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await services.delete_subscriber(id, current_user, db)
    return None

@router.post("/{id}/pause", response_model=schemas.SubscriberResponse)
async def pause_subscriber(
    id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await services.pause_subscriber(id, current_user, db)

@router.post("/{id}/resume", response_model=schemas.SubscriberResponse)
async def resume_subscriber(
    id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await services.resume_subscriber(id, current_user, db, redis)

@router.get("/{id}/deliveries", response_model=schemas.DeliveryListResponse)
async def get_subscriber_deliveries(
    id: uuid.UUID,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await services.get_deliveries(id, tenant_id, db, status, page, limit)

@router.post("/{id}/test")
async def test_subscriber(
    id: uuid.UUID,
    payload: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await services.test_subscriber(id, payload, current_user, db, redis)

@router.post("/deliveries/{delivery_id}/retry")

async def retry_delivery(
    delivery_id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await services.retry_delivery(delivery_id, current_user, db, redis)
