import asyncio
import os
import sys
import uuid
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.common.db import AsyncSessionLocal
from app.models import Application

async def get_client_id():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Application).order_by(Application.created_at))
        apps = result.scalars().all()
        for app in apps:
            print(f"App Name: {app.name}, Client ID: {app.client_id}")

if __name__ == "__main__":
    asyncio.run(get_client_id())
