import asyncio
import os
import sys
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.common.db import AsyncSessionLocal
from app.models import Event, Delivery

async def check_event_status():
    async with AsyncSessionLocal() as db:
        event_id = '406a9c0c-58f1-441f-8fe1-001f6018e241'
        res = await db.execute(select(Event).where(Event.id == event_id))
        event = res.scalar_one_or_none()
        if not event:
            print("Event not found")
            return

        print(f"Event ID: {event.id}")
        print(f"Processed At: {event.processed_at}")
        
        res = await db.execute(select(Delivery).where(Delivery.event_id == event_id))
        deliveries = res.scalars().all()
        print(f"Deliveries: {len(deliveries)}")
        for d in deliveries:
            print(f"  - Sub: {d.subscriber_id}, Status: {d.status}, HTTP: {d.http_status}")

if __name__ == "__main__":
    asyncio.run(check_event_status())
