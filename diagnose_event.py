
import asyncio
import uuid
from sqlalchemy import select
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Override DB URL for local execution
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5434/webhook_service"
os.environ["REDIS_URL"] = "redis://localhost:6381/0"

from app.models import Event, Subscriber, Application, Delivery
from app.models.base import Base

# Manually create a session for local use
engine = create_async_engine(os.environ["DATABASE_URL"])
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check_event_status(event_id_str):
    async with AsyncSessionLocal() as db:
        event_id = uuid.UUID(event_id_str)
        
        # Check Event
        event_res = await db.execute(select(Event).where(Event.id == event_id))
        event = event_res.scalar_one_or_none()
        if not event:
            print(f"Event {event_id_str} not found in DB")
            return

        print(f"Event ID: {event.id}")
        print(f"Event Type: {event.event_type}")
        print(f"Target App ID: {event.target_app_id}")
        print(f"Tenant ID: {event.tenant_id}")
        print(f"Processed At: {event.processed_at}")

        # Check Subscribers for this tenant
        sub_res = await db.execute(select(Subscriber).where(Subscriber.tenant_id == event.tenant_id))
        subs = sub_res.scalars().all()
        print(f"\nSubscribers for tenant {event.tenant_id}:")
        for s in subs:
            print(f"  - ID: {s.id}, Name: {s.name}, Status: {s.status}, Events: {s.events}")
            # Check if this sub has an application with the target_app_id if it exists
            app_res = await db.execute(select(Application).where(Application.subscriber_id == s.id))
            apps = app_res.scalars().all()
            for a in apps:
                print(f"    - Application Client ID: {a.client_id}")

        # Check Deliveries
        del_res = await db.execute(select(Delivery).where(Delivery.event_id == event_id))
        deliveries = del_res.scalars().all()
        print(f"\nDeliveries for event {event_id_str}:")
        if not deliveries:
            print("  No deliveries found.")
        for d in deliveries:
            print(f"  - ID: {d.id}, Subscriber ID: {d.subscriber_id}, Status: {d.status}, HTTP Status: {d.http_status}")

if __name__ == "__main__":
    event_id = "0a7d28b8-bdad-412d-80c0-12f15d1620b7"
    asyncio.run(check_event_status(event_id))
