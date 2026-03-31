import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr
from app.models import User, Tenant, AuditLog, Invitation
from app.common.email import send_notification_email  # We'll use the existing email helper

class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "viewer"

class RegisterInvitedRequest(BaseModel):
    token: str
    password: str
    first_name: str
    last_name: str

async def invite_member(tenant_id: uuid.UUID, data: InviteMemberRequest, actor_email: str, db: AsyncSession):
    # Check if already invited or member (simplified)
    # ... logic here ...
    
    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        tenant_id=tenant_id,
        email=data.email,
        role=data.role,
        token=token,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    )
    db.add(invitation)
    
    # Audit log
    audit = AuditLog(
        tenant_id=tenant_id,
        actor=actor_email,
        action="user.invited",
        context_metadata={"email": data.email, "role": data.role}
    )
    db.add(audit)
    await db.commit()
    
    # Send email (mocking the template logic for now)
    # url = f"{settings.FRONTEND_URL}/accept-invite/{token}"
    # await send_notification_email(...)
    return invitation

async def accept_invite(token: str, data: RegisterInvitedRequest, db: AsyncSession):
    stmt = select(Invitation).where(
        and_(
            Invitation.token == token,
            Invitation.expires_at > datetime.now(timezone.utc).replace(tzinfo=None),
            Invitation.accepted_at == None
        )
    )
    res = await db.execute(stmt)
    invitation = res.scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")
    
    # Check if user exists
    user_stmt = select(User).where(User.email == invitation.email)
    res = await db.execute(user_stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        # Create new user
        # from app.common.security import get_password_hash
        user = User(
            email=invitation.email,
            first_name=data.first_name,
            last_name=data.last_name,
            # hashed_password=get_password_hash(data.password),
            is_active=True
        )
        db.add(user)
        await db.flush()
    
    # Add to tenant (assuming many-to-many or single-tenant with role)
    # For now, we assume user model has a primary tenant or we add to a mapping table
    # ... logic here ...
    
    invitation.accepted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Audit
    audit = AuditLog(
        tenant_id=invitation.tenant_id,
        actor=invitation.email,
        action="user.joined",
        resource_id=user.id
    )
    db.add(audit)
    await db.commit()
    return user

async def list_members(tenant_id: uuid.UUID, db: AsyncSession):
    # This depends on your User-Tenant relationship
    # Assuming users have a tenant_id for now or a join table
    # ...
    return []

async def revoke_member(tenant_id: uuid.UUID, user_id: uuid.UUID, actor_email: str, db: AsyncSession):
    # Soft revoke or delete mapping
    # ...
    audit = AuditLog(
        tenant_id=tenant_id,
        actor=actor_email,
        action="user.revoked",
        resource_id=user_id
    )
    db.add(audit)
    await db.commit()
    return True
