import asyncio
import os
import sys
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.common.db import AsyncSessionLocal
from app.models import Application, Subscriber

async def check_sub():
    async with AsyncSessionLocal() as db:
        sub_id = '8f628d92-28e6-41cd-9396-3fa828bb487f'
        res = await db.execute(select(Application).where(Application.subscriber_id == sub_id))
        app = res.scalar_one_or_none()
        if app:
            print(f"Subscriber {sub_id} is linked to App: {app.client_id}")
        else:
            print(f"Subscriber {sub_id} is NOT LINKED to any app")

if __name__ == "__main__":
    asyncio.un(check_sub())
