import hmac
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Form, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from app.common.db import get_db
from app.common.crypto import decrypt_secret
from app.config.settings import settings
from app.models import Application

router = APIRouter(prefix="/oauth", tags=["OAuth2 M2M"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str

@router.post("/token", response_model=TokenResponse)
async def generate_m2m_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form("webhooks:publish"),
    db: AsyncSession = Depends(get_db)
):
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")
    
    # Scope check
    if scope != "webhooks:publish":
        raise HTTPException(status_code=400, detail="Invalid scope")

    # Fetch app
    result = await db.execute(select(Application).where(Application.client_id == client_id))
    app = result.scalar_one_or_none()
    
    if not app or app.status == "deleted":
        raise HTTPException(status_code=401, detail="Invalid client_id")
    
    if app.type not in ["producer", "hybrid"]:
        raise HTTPException(status_code=403, detail="Application is not a producer")

    # Verify secret
    try:
        decrypted_secret = decrypt_secret(app.client_secret_enc, settings.ENCRYPTION_KEY).decode()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to verify credentials")
    
    if not hmac.compare_digest(decrypted_secret, client_secret):
        raise HTTPException(status_code=401, detail="Invalid client_secret")

    # Generate M2M Token
    payload = {
        "sub": client_id,
        "tenant_id": str(app.tenant_id),
        "scope": scope,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "m2m": True
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return TokenResponse(
        access_token=token,
        scope=scope
    )
