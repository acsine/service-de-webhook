import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.common.db import get_db
from app.common.redis import get_redis
from app.common.auth import get_current_user
from app.services.applications import services, schemas

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("", response_model=schemas.ApplicationCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: schemas.CreateApplicationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await services.create_application(data, current_user, db, redis)

@router.get("", response_model=List[schemas.ApplicationResponse])
async def list_applications(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await services.list_applications(tenant_id, db)

@router.get("/{id}", response_model=schemas.ApplicationResponse)
async def get_application(
    id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await services.get_application(id, tenant_id, db)

@router.patch("/{id}", response_model=schemas.ApplicationResponse)
async def update_application(
    id: uuid.UUID,
    data: schemas.UpdateApplicationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await services.update_application(id, data, current_user, db)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await services.delete_application(id, current_user, db)
    return None

@router.post("/{id}/rotate-secret")
async def rotate_secret(
    id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    return await services.rotate_secret(id, current_user, db, redis)

@router.get("/{id}/stats")
async def get_application_stats(
    id: uuid.UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await services.get_application_stats(id, tenant_id, db)
