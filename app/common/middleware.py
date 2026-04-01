import time
import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import Request as FastAPIRequest
from app.common.redis import get_redis

logger = structlog.get_logger()

class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Convert headers list to dict for easier manipulation
                headers = dict(message.get("headers", []))
                headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                headers[b"x-content-type-options"] = b"nosniff"
                headers[b"x-frame-options"] = b"DENY"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                # Update message headers
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_wrapper)

class StructlogMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = int((time.perf_counter() - start_time) * 1000)
                status_code = message["status"]
                path = scope.get("path", "")
                method = scope.get("method", "")
                ip = scope.get("client", ["unknown"])[0] if scope.get("client") else "unknown"
                
                logger.info(
                    "request_finished",
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration,
                    ip=ip
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)

class GlobalRateLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/api/v1/auth/"):
            await self.app(scope, receive, send)
            return
            
        if path == "/api/v1/auth/refresh":
            await self.app(scope, receive, send)
            return

        ip = scope.get("client", ["unknown"])[0] if scope.get("client") else "unknown"
        key = f"rl:ip:{ip}"
        
        # In a real app, we'd use a shared redis pool
        from app.common.redis import _redis as redis 
        if redis:
            try:
                count = await redis.incr(key)
                if count == 1:
                    await redis.expire(key, 60)
                
                if count > 100:
                    response_start = {
                        "type": "http.response.start",
                        "status": 429,
                        "headers": [[b"content-type", b"text/plain"]],
                    }
                    await send(response_start)
                    await send({
                        "type": "http.response.body",
                        "body": b"Rate limit exceeded",
                    })
                    return
            except Exception as e:
                # Fallback on redis error to not block requests
                logger.error("redis_rate_limit_error", error=str(e))
                
        await self.app(scope, receive, send)
