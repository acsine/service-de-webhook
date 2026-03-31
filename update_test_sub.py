import asyncio
import os
import sys
sys.path.append(os.getcwd())

from sqlalchemy import select, update
from app.common.db import AsyncSessionLocal
from app.models import Subscriber

async def update_sub():
    async with AsyncSessionLocal() as db:
        # Update our test subscriber to include '*' to catch all events
        await db.execute(
            update(Subscriber)
            .where(Subscriber.id == '8f628d92-28e6-41cd-9396-3fa828bb487f')
            .values(events=['*'])
        )
        await db.commit()
        print("Updated subscriber 8f628d92 to listen to all events (*)")

if __name__ == "__main__":
    asyncio.run(update_sub())
