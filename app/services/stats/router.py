from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.db import get_db
from app.common.redis import get_redis
from app.common.auth import get_current_user
from app.services.stats import services as stats_service
from app.services.stats.schemas import Period, Granularity
import uuid

router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.get("/overview")
async def get_overview(
    period: Period = Query(Period.P24H),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await stats_service.get_overview(tenant_id, period, db, redis)

@router.get("/events-by-type")
async def get_events_by_type(
    period: Period = Query(Period.P7D),
    app_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await stats_service.get_events_by_type(tenant_id, period, app_id, db, redis)

@router.get("/delivery-rates")
async def get_delivery_rates(
    period: Period = Query(Period.P24H),
    granularity: Granularity = Query(Granularity.HOUR),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await stats_service.get_delivery_rates(tenant_id, period, granularity, db, redis)

@router.get("/latency")
async def get_latency(
    period: Period = Query(Period.P24H),
    granularity: Granularity = Query(Granularity.HOUR),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await stats_service.get_latency(tenant_id, period, granularity, db, redis)

@router.get("/subscribers/top")
async def get_top_subscribers(
    period: Period = Query(Period.P7D),
    limit: int = Query(10),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await stats_service.get_top_subscribers(tenant_id, period, limit, db, redis)

@router.get("/export")
async def export_stats(
    period: Period = Query(Period.P30D),
    format: str = Query("csv", pattern="^(csv|json)$"),
    subscriber_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await stats_service.export_stats(tenant_id, period, format, subscriber_id, db)
