from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# Default to a mock URL if DATABASE_URL is not provided yet to prevent startup crash
db_url = settings.DATABASE_URL or "postgresql+asyncpg://user:pass@localhost/db"
engine = create_async_engine(db_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
