import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from mangum import Mangum

from app.common.redis import init_redis, close_redis
from sqlalchemy import text
from app.common.db import engine
from app.models.base import Base
from app.common.exception_handler import http_exception_handler, validation_exception_handler
from app.config.settings import settings

# Import existing routers
# Note: Adjusting imports based on existing project structure
try:
    from app.services.welcome.router import router as welcome_router
except ImportError:
    from app.services.welcome import router as welcome_router

try:
    from app.services.countries.router import router as countries_router
except ImportError:
    from app.services.countries import router as countries_router

from app.services.applications.router import router as applications_router
from app.services.subscribers.router import router as subscribers_router
from app.services.oauth.router import router as oauth_router
from app.services.events.router import router as events_router
from app.services.stats.router import router as stats_router
from app.services.audit.router import router as audit_router
from app.services.team.router import router as team_router
from app.common.middleware import SecurityHeadersMiddleware, StructlogMiddleware, GlobalRateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis
    print(f"Starting application in {settings.ENV} mode...")
    try:
        print("Connecting to Redis...")
        await init_redis()
        print("Redis connected successfully.")
    except Exception as e:
        print(f"WARNING: Could not connect to Redis at startup: {e}")
    
    # Create tables in development
    if settings.ENV == "development":
        try:
            print("Running database migrations/create_all...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database initialized.")
        except Exception as e:
            print(f"ERROR during database initialization: {e}")
            
    yield
    # Shutdown: Close Redis
    try:
        await close_redis()
    except:
        pass

app = FastAPI(
    title="Centralized Webhook Service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
origins = [settings.FRONTEND_URL]
if settings.ENV == "development":
    origins.append("http://localhost:3000")
    origins.append("http://127.0.0.1:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(StructlogMiddleware)
app.add_middleware(GlobalRateLimitMiddleware)

# Exception Handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return await http_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def form_validation_exception_handler(request, exc):
    return await validation_exception_handler(request, exc)

# Global Prefix /api/v1 for business routes
api_v1_router = APIRouter(prefix="/api/v1")

# Include existing routers in v1
# Note: welcome_router might not be a business route but we include it for compatibility
api_v1_router.include_router(welcome_router, tags=["Welcome"])
api_v1_router.include_router(countries_router, tags=["Countries"])
api_v1_router.include_router(applications_router)
api_v1_router.include_router(subscribers_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(stats_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(team_router)

app.include_router(oauth_router)
app.include_router(api_v1_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Centralized Webhook Service API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    from app.common.redis import _redis as redis
    from app.common.db import engine
    
    redis_status = "ok" if redis else "error"
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except:
        db_status = "error"
        
    return {
        "status": "ok" if redis_status == "ok" and db_status == "ok" else "degraded",
        "version": "1.0.0",
        "services": {
            "database": db_status,
            "redis": redis_status
        }
    }

# Compatibility with Lambda
handler = Mangum(app)
