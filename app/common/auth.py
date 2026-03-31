from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config.settings import settings

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        credentials: Optional[HTTPAuthorizationCredentials] = await super(JWTBearer, self).__call__(request)
        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")
            return self.verify_token(credentials.credentials)
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization credentials")

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid token or expired")

async def get_current_user(payload: Dict[str, Any] = Depends(JWTBearer())) -> Dict[str, Any]:
    """
    Dependency to get the current user from JWT payload.
    Expected payload keys: 'sub' (user_id), 'tenant_id', 'role'.
    """
    if not payload or "tenant_id" not in payload:
        raise HTTPException(status_code=401, detail="Invalid user session")
    return payload