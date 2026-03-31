import time
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import Request as FastAPIRequest
from app.common.redis import get_redis

logger = structlog.get_logger()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

class StructlogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        response = await call_next(request)
        
        duration = int((time.perf_counter() - start_time) * 1000)
        
        # Masking logic simplified
        path = request.url.path
        method = request.method
        status_code = response.status_code
        
        logger.info(
            "request_finished",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration,
            ip=request.client.host if request.client else "unknown"
        )
        return response

class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/v1/auth/"):
            return await call_next(request)
            
        if request.url.path == "/api/v1/auth/refresh":
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        key = f"rl:ip:{ip}"
        
        # In a real app, we'd use a shared redis pool
        # Here we mock it or use a global one
        from app.common.redis import _redis as redis 
        if redis:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)
            
            if count > 100:
                return Response(content="Rate limit exceeded", status_code=429)
                
        return await call_next(request)
