import asyncio
import os
import sys
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.common.db import AsyncSessionLocal
from app.models import Subscriber

async def list_subs():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Subscriber))
        subs = result.scalars().all()
        for s in subs:
            print(f"ID: {s.id}, Name: {s.name}, Events: {s.events}")

if __name__ == "__main__":
    asyncio.run(list_subs())
