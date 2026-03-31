
import asyncio
import os
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Override DB URL for local execution
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5434/webhook_service"

from app.models import Subscriber, Application

async def list_subs():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Subscriber))
        subs = res.scalars().all()
        print(f"Total Subscribers: {len(subs)}")
        for s in subs:
            print(f"ID: {s.id}")
            print(f"  Name: {s.name}")
            print(f"  Events: {s.events}")
            print(f"  Status: {s.status}")
            print(f"  Tenant ID: {s.tenant_id}")
            
            app_res = await db.execute(select(Application).where(Application.subscriber_id == s.id))
            apps = app_res.scalars().all()
            for a in apps:
                print(f"    - Application Client ID: {a.client_id}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(list_subs())
