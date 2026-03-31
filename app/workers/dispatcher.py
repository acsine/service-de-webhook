import asyncio
import json
import time
import hmac
import hashlib
import httpx
import uuid
from datetime import datetime, timezone
import structlog
from sqlalchemy import select, update, and_
from app.common.db import AsyncSessionLocal
from app.models import Event, Subscriber, Delivery, AuditLog
from app.common.crypto import decrypt_secret
from app.config.settings import settings
from app.core.circuit_breaker import CircuitBreakerService

logger = structlog.get_logger()

async def dispatch_event(ctx, event_id: str):
    async with AsyncSessionLocal() as db:
        logger.info("event.dispatch_start", event_id=event_id)
        result = await db.execute(select(Event).where(Event.id == uuid.UUID(event_id)))
        event = result.scalar_one_or_none()
        if not event or event.processed_at:
            logger.info("event.already_processed", event_id=event_id)
            return f"Event {event_id} already processed or missing"

        sub_query = select(Subscriber).where(
            and_(
                Subscriber.status.in_(["active", "paused"]), # Include paused for half-open check
                Subscriber.tenant_id == event.tenant_id
            )
        )
        if event.target_app_id:
            from app.models.application import Application
            sub_query = sub_query.join(Application, Application.subscriber_id == Subscriber.id).where(
                Application.client_id == event.target_app_id
            )
        
        sub_result = await db.execute(sub_query)

        all_subs = sub_result.scalars().all()
        
        subscribers = [s for s in all_subs if event.event_type in s.events or "*" in s.events]

        if not subscribers:
            logger.info("event.no_subscribers", event_id=event_id, event_type=event.event_type, target_app_id=event.target_app_id)
            event.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()
            return f"No active subscribers for event {event_id}"

        redis = ctx['redis']
        tasks = [deliver_to_subscriber(ctx, db, redis, event, sub) for sub in subscribers]
        await asyncio.gather(*tasks, return_exceptions=True)

        event.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        logger.info("event.dispatch_finished", event_id=event_id, recipients=len(subscribers))
        return f"Dispatched event {event_id} to {len(subscribers)} subscribers"

async def deliver_to_subscriber(ctx, db, redis, event, subscriber):
    # Half-Open Check
    is_half_open = await CircuitBreakerService.check_half_open(subscriber.id, redis, subscriber.status)
    
    if subscriber.status == "paused" and not is_half_open:
        return

    delivery = Delivery(
        event_id=event.id,
        subscriber_id=subscriber.id,
        status='pending',
        attempt_number=1
    )
    db.add(delivery)
    await db.flush()

    try:
        secret_bytes = decrypt_secret(subscriber.secret_hmac_enc, settings.ENCRYPTION_KEY)
        
        webhook_id = str(uuid.uuid4())
        ts = int(time.time())
        payload = {
            "webhook_id": webhook_id,
            "event_type": event.event_type,
            "tenant_id": str(event.tenant_id),
            "timestamp": ts,
            "payload": event.payload
        }

        raw_body = json.dumps(payload, separators=(",", ":")).encode()
        sig = hmac.new(secret_bytes, f"{ts}.{raw_body.decode()}".encode(), hashlib.sha256).hexdigest()
        header_value = f"t={ts},v1={sig}"
        delivery.signature = header_value

        start_time = time.perf_counter()
        headers = {
            "X-Webhook-Signature": header_value,
            "X-Webhook-Timestamp": str(ts),
            "X-Webhook-Event": event.event_type,
            "X-Webhook-ID": webhook_id,
            "X-Webhook-Attempt": "1",
            "Content-Type": "application/json",
            "User-Agent": "WebhookService/1.0"
        }

        async with httpx.AsyncClient(timeout=subscriber.timeout_ms / 1000) as client:
            resp = await client.post(subscriber.callback_url, data=raw_body, headers=headers)
            duration = int((time.perf_counter() - start_time) * 1000)
            
            delivery.http_status = resp.status_code
            delivery.duration_ms = duration
            
            log_context = {
                "event_id": str(event.id),
                "subscriber_id": str(subscriber.id),
                "callback_url": subscriber.callback_url,
                "status": resp.status_code,
                "duration_ms": duration
            }

            if 200 <= resp.status_code < 300:
                logger.info("webhook.delivery_success", **log_context)
                delivery.status = 'success'
                delivery.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)
                await CircuitBreakerService.close_circuit(subscriber.id, redis, db)
            else:
                logger.warning("webhook.delivery_failed", **log_context)
                delivery.status = 'failed'
                delivery.response_body = resp.text[:1000]
                await handle_failure(ctx, db, redis, subscriber, delivery, is_half_open)
                
    except Exception as e:
        delivery.status = 'failed'
        delivery.response_body = str(e)[:1000]
        await handle_failure(ctx, db, redis, subscriber, delivery, is_half_open)

async def handle_failure(ctx, db, redis, subscriber, delivery, is_half_open):
    if is_half_open:
        # HALF_OPEN test failed -> Retour OPEN (stay paused for 1h)
        await CircuitBreakerService.reset_open(subscriber.id, redis)
    else:
        await CircuitBreakerService.increment_failure(subscriber.id, redis, db)
    
    # Enqueue retry
    await ctx['pool'].enqueue_job(
        "retry_delivery",
        delivery_id=str(delivery.id),
        attempt=1,
        _defer_by=1 # Immediate retry (0s delay roughly)
    )
