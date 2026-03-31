from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.db import get_db
from app.common.auth import get_current_user
from app.services.audit import services as audit_service
from app.services.audit.services import AuditLogFilters
import uuid

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("/")
async def list_audit_logs(
    filters: AuditLogFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # check role owner here...
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await audit_service.list_audit_logs(tenant_id, filters, db)

@router.get("/export")
async def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|json)$"),
    filters: AuditLogFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await audit_service.export_audit_logs(tenant_id, filters, format, db)
