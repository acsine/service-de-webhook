import asyncio
import os
import sys
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.common.db import AsyncSessionLocal
from app.models import Application, Subscriber

async def list_links():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Application))
        apps = res.scalars().all()
        for a in apps:
            print(f"App ClientID: {a.client_id}, SubscriberID: {a.subscriber_id}")

if __name__ == "__main__":
    asyncio.run(list_links())
