from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.db import get_db
from app.common.auth import get_current_user
from app.services.team import services as team_service
from app.services.team.services import InviteMemberRequest, RegisterInvitedRequest
import uuid

router = APIRouter(prefix="/team", tags=["Team Management"])

@router.post("/invite")
async def invite_member(
    data: InviteMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await team_service.invite_member(tenant_id, data, current_user["email"], db)

@router.post("/accept-invite/{token}")
async def accept_invite(
    token: str,
    data: RegisterInvitedRequest,
    db: AsyncSession = Depends(get_db)
):
    return await team_service.accept_invite(token, data, db)

@router.get("/members")
async def list_members(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await team_service.list_members(tenant_id, db)

@router.delete("/members/{user_id}")
async def revoke_member(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    tenant_id = uuid.UUID(current_user["tenant_id"])
    return await team_service.revoke_member(tenant_id, user_id, current_user["email"], db)
