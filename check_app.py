import asyncio
import os
import sys
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.common.db import AsyncSessionLocal
from app.models import Application

async def check_app():
    async with AsyncSessionLocal() as db:
        client_id = 'app_18967e96'
        res = await db.execute(select(Application).where(Application.client_id == client_id))
        app = res.scalar_one_or_none()
        if app:
            print(f"App {client_id} FOUND (SubscriberID: {app.subscriber_id})")
        else:
            print(f"App {client_id} NOT FOUND")

if __name__ == "__main__":
    asyncio.run(check_app())
