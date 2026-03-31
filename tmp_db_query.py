import asyncio
import os
import sys
import uuid
# Ensure app is in path
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.common.db import AsyncSessionLocal
from app.models import Application

async def get_client_id():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Application).order_by(Application.created_at))
            app = result.scalars().first()
            if app:
                print(f"CLIENT_ID={app.client_id}")
            else:
                print("NOT_FOUND")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(get_client_id())
