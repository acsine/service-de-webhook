import secrets
import uuid
import base64
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models import Application, Subscriber, AuditLog, Event, Delivery
from app.services.applications.schemas import (
    CreateApplicationRequest, UpdateApplicationRequest, 
    ApplicationResponse, ApplicationCreatedResponse, ApplicationType
)
from app.common.crypto import encrypt_secret, decrypt_secret
from app.config.settings import settings
from redis.asyncio import Redis

async def create_application(
    data: CreateApplicationRequest, 
    current_user: Dict[str, Any], 
    db: AsyncSession, 
    redis: Redis
) -> ApplicationCreatedResponse:
    tenant_id = uuid.UUID(current_user["tenant_id"])
    
    # Handle sub as UUID (user) or string (M2M)
    user_id = None
    sub_val = current_user.get("sub")
    if sub_val:
        try:
            user_id = uuid.UUID(sub_val)
        except (ValueError, TypeError):
            user_id = None
    
    client_secret_raw = None
    secret_hmac_raw = None
    subscriber_id = None
    client_id = None
    client_secret_enc = None

    # PRODUCER / HYBRID logic
    if data.type in [ApplicationType.PRODUCER, ApplicationType.HYBRID]:
        client_id = f"app_{secrets.token_hex(4)}"
        client_secret_raw = secrets.token_urlsafe(48)
        client_secret_enc, _ = encrypt_secret(client_secret_raw.encode(), settings.ENCRYPTION_KEY)

    # CONSUMER / HYBRID logic
    if data.type in [ApplicationType.CONSUMER, ApplicationType.HYBRID]:
        if not data.callback_url or not data.callback_url.startswith("https://"):
            raise HTTPException(status_code=400, detail="callback_url is required and must be HTTPS")
        
        # Challenge verification
        if data.verify_url:
            challenge = str(uuid.uuid4())
            async with httpx.AsyncClient(timeout=5.0) as client:
                try:
                    resp = await client.get(data.callback_url, params={"webhook_challenge": challenge})
                    if resp.status_code != 200:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Callback URL returned status {resp.status_code}. Expected 200."
                        )
                    
                    resp_json = resp.json()
                    if resp_json.get("challenge") != challenge:
                        raise HTTPException(
                            status_code=400, 
                            detail="Webhook challenge verification failed: 'challenge' field mismatch."
                        )
                except httpx.TimeoutException:
                    raise HTTPException(status_code=400, detail="Callback URL verification timed out (5s limit).")
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Failed to verify callback URL: {str(e)}")

        secret_hmac_raw_bytes = secrets.token_bytes(32)
        secret_hmac_raw = base64.b64encode(secret_hmac_raw_bytes).decode('utf-8')
        secret_hmac_enc, _ = encrypt_secret(secret_hmac_raw_bytes, settings.ENCRYPTION_KEY)
        
        subscriber = Subscriber(
            tenant_id=tenant_id,
            name=data.name,
            callback_url=data.callback_url,
            secret_hmac_enc=secret_hmac_enc,
            secret_hmac_key_id="v1",
            events=data.events or [],
            verified_at=datetime.utcnow()
        )
        db.add(subscriber)
        await db.flush()
        subscriber_id = subscriber.id

    application = Application(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        type=data.type,
        client_id=client_id,
        client_secret_enc=client_secret_enc,
        subscriber_id=subscriber_id,
        created_by=user_id
    )
    db.add(application)
    
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor=str(current_user.get("sub", "system")),
        action="application.created",
        resource_id=None,
        context_metadata={"name": data.name, "type": data.type}
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(application)
    
    response = ApplicationCreatedResponse.model_validate(application)
    response.client_secret = client_secret_raw
    response.secret_hmac = secret_hmac_raw
    return response

async def list_applications(tenant_id: uuid.UUID, db: AsyncSession) -> List[Application]:
    result = await db.execute(
        select(Application).where(Application.tenant_id == tenant_id, Application.status != "deleted")
    )
    return list(result.scalars().all())

async def get_application(app_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession) -> Application:
    result = await db.execute(
        select(Application).where(Application.id == app_id, Application.tenant_id == tenant_id)
    )
    app = result.scalar_one_or_none()
    if not app or app.status == "deleted":
        raise HTTPException(status_code=404, detail="Application not found")
    return app

async def update_application(app_id: uuid.UUID, data: UpdateApplicationRequest, current_user: Dict[str, Any], db: AsyncSession) -> Application:
    tenant_id = uuid.UUID(current_user["tenant_id"])
    app = await get_application(app_id, tenant_id, db)
    
    if data.name: app.name = data.name
    if data.description: app.description = data.description
    if data.status: app.status = data.status
    
    await db.commit()
    await db.refresh(app)
    return app

async def rotate_secret(
    app_id: uuid.UUID, 
    current_user: Dict[str, Any], 
    db: AsyncSession, 
    redis: Redis
) -> Dict[str, str]:
    tenant_id = uuid.UUID(current_user["tenant_id"])
    app = await get_application(app_id, tenant_id, db)
    
    resp = {}
    
    if app.type in [ApplicationType.PRODUCER, ApplicationType.HYBRID]:
        new_secret_raw = secrets.token_urlsafe(48)
        new_secret_enc, _ = encrypt_secret(new_secret_raw.encode(), settings.ENCRYPTION_KEY)
        app.client_secret_enc = new_secret_enc
        resp["client_secret"] = new_secret_raw
        
    if app.type in [ApplicationType.CONSUMER, ApplicationType.HYBRID]:
        subscriber_result = await db.execute(select(Subscriber).where(Subscriber.id == app.subscriber_id))
        sub = subscriber_result.scalar_one()
        
        # Grace period for old secret
        old_secret_raw_bytes = decrypt_secret(sub.secret_hmac_enc, settings.ENCRYPTION_KEY)
        old_secret_b64 = base64.b64encode(old_secret_raw_bytes).decode('utf-8')
        await redis.setex(f"hmac:grace:{sub.id}", 86400, old_secret_b64)
        
        new_secret_bytes = secrets.token_bytes(32)
        new_secret_b64 = base64.b64encode(new_secret_bytes).decode('utf-8')
        new_secret_enc, _ = encrypt_secret(new_secret_bytes, settings.ENCRYPTION_KEY)
        sub.secret_hmac_enc = new_secret_enc
        resp["secret_hmac"] = new_secret_b64

    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor=str(current_user.get("sub", "system")),
        action="secret.rotated",
        resource_id=app.id
    )
    db.add(audit_log)
    await db.commit()
    return resp

async def delete_application(app_id: uuid.UUID, current_user: Dict[str, Any], db: AsyncSession):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    app = await get_application(app_id, tenant_id, db)
    app.status = "deleted"
    
    audit_log = AuditLog(
        tenant_id=tenant_id,
        actor=str(current_user.get("sub", "system")),
        action="application.deleted",
        resource_id=app.id
    )
    db.add(audit_log)
    await db.commit()

async def get_application_stats(app_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    app = await get_application(app_id, tenant_id, db)
    stats = {"app_id": str(app_id), "type": app.type}
    
    if app.type in [ApplicationType.PRODUCER, ApplicationType.HYBRID]:
        res = await db.execute(select(func.count(Event.id)).where(Event.source_app == app.client_id))
        stats["events_count"] = res.scalar()
        
    if app.type in [ApplicationType.CONSUMER, ApplicationType.HYBRID]:
        res = await db.execute(select(func.count(Delivery.id)).where(Delivery.subscriber_id == app.subscriber_id))
        stats["deliveries_count"] = res.scalar()
        
    return stats
