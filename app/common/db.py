from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.config.settings import settings

# Default to a mock URL if DATABASE_URL is not provided yet to prevent startup crash
db_url = settings.DATABASE_URL or "postgresql+asyncpg://user:pass@localhost/db"

# In serverless environments (Vercel/Lambda), NullPool is recommended 
# to avoid OSError: [Errno 16] Device or resource busy which happens 
# when uvloop manages SSL sockets in suspended/resumed processes.
engine = create_async_engine(
    db_url,
    poolclass=NullPool,
    connect_args={"ssl": "require"} if "localhost" not in db_url else {}
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
