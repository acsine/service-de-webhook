import json
import csv
import io
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

class AuditLogFilters(BaseModel):
    action: Optional[str] = None
    actor: Optional[str] = None
    resource_id: Optional[str] = None
    page: int = 1
    limit: int = 50

async def list_audit_logs(tenant_id: uuid.UUID, filters: AuditLogFilters, db: AsyncSession):
    from app.models import AuditLog
    query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
    
    if filters.action:
        query = query.where(AuditLog.action == filters.action)
    if filters.actor:
        query = query.where(AuditLog.actor == filters.actor)
    if filters.resource_id:
        query = query.where(AuditLog.resource_id == uuid.UUID(filters.resource_id))
        
    # Count total
    count_stmt = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0
    
    # Paginate
    query = query.order_by(AuditLog.created_at.desc()).offset((filters.page - 1) * filters.limit).limit(filters.limit)
    res = await db.execute(query)
    items = res.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "limit": filters.limit,
        "has_next": total > filters.page * filters.limit
    }

async def export_audit_logs(tenant_id: uuid.UUID, filters: AuditLogFilters, format: str, db: AsyncSession):
    from app.models import AuditLog
    query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
    # Applying filters similarly...
    
    if format == "csv":
        async def generate_csv():
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["id", "actor", "action", "resource_id", "created_at", "metadata"])
            yield output.getvalue()
            output.truncate(0)
            output.seek(0)
            
            res = await db.stream(query)
            async for row in res:
                writer.writerow([str(row.AuditLog.id), row.AuditLog.actor, row.AuditLog.action, str(row.AuditLog.resource_id), row.AuditLog.created_at, json.dumps(row.AuditLog.context_metadata)])
                yield output.getvalue()
                output.truncate(0)
                output.seek(0)
        return StreamingResponse(generate_csv(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=audit_logs.csv"})
    else: # ndjson
        async def generate_json():
            res = await db.stream(query)
            async for row in res:
                item = {
                    "id": str(row.AuditLog.id),
                    "actor": row.AuditLog.actor,
                    "action": row.AuditLog.action,
                    "resource_id": str(row.AuditLog.resource_id),
                    "created_at": row.AuditLog.created_at.isoformat(),
                    "metadata": row.AuditLog.context_metadata
                }
                yield json.dumps(item) + "\n"
        return StreamingResponse(generate_json(), media_type="application/x-ndjson", headers={"Content-Disposition": "attachment; filename=audit_logs.json"})
