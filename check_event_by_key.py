import asyncio
import os
import sys
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.common.db import AsyncSessionLocal
from app.models import Event, Delivery

async def check_event_by_key():
    async with AsyncSessionLocal() as db:
        key = 'test_unique_final_logged_200'
        res = await db.execute(select(Event).where(Event.idempotency_key == key))
        event = res.scalar_one_or_none()
        if not event:
            print("Event not found")
            return

        print(f"Event ID: {event.id}")
        print(f"Processed At: {event.processed_at}")
        
        res = await db.execute(select(Delivery).where(Delivery.event_id == event.id))
        deliveries = res.scalars().all()
        print(f"Deliveries: {len(deliveries)}")

if __name__ == "__main__":
    asyncio.run(check_event_by_key())
