from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import settings
from app.common.db import get_db
from app.models import Application

class M2MBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Dict[str, Any]:
        credentials: Optional[HTTPAuthorizationCredentials] = await super(M2MBearer, self).__call__(request)
        if not credentials or credentials.scheme != "Bearer":
            raise HTTPException(status_code=403, detail="Invalid auth scheme")
        
        try:
            payload = jwt.decode(token=credentials.credentials, key=settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            if not payload.get("m2m"):
                raise HTTPException(status_code=403, detail="Not a Machine-to-Machine token")
            if payload.get("scope") != "webhooks:publish":
                raise HTTPException(status_code=403, detail="Insufficient scope")
            return payload
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid or expired M2M token")

async def get_producer_app(
    payload: Dict[str, Any] = Depends(M2MBearer()),
    db: AsyncSession = Depends(get_db)
) -> Application:
    client_id = payload.get("sub")
    result = await db.execute(select(Application).where(Application.client_id == client_id))
    app = result.scalar_one_or_none()
    
    if not app or app.status == "deleted":
        raise HTTPException(status_code=401, detail="Producer application not found")
        
    return app
