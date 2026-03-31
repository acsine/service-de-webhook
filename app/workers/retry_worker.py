import asyncio
import json
import time
import hmac
import hashlib
import httpx
import uuid
from datetime import datetime, timezone, timedelta
import structlog
from sqlalchemy import select, update
from app.common.db import AsyncSessionLocal
from app.models import Event, Subscriber, Delivery, AuditLog
from app.common.crypto import decrypt_secret
from app.config.settings import settings
from app.services.events.constants import CIRCUIT_BREAKER_THRESHOLD
from app.core.circuit_breaker import CircuitBreakerService

logger = structlog.get_logger()

async def retry_delivery(ctx, delivery_id: str, attempt: int):
    async with AsyncSessionLocal() as db:
        # 1. Fetch Delivery
        result = await db.execute(select(Delivery).where(Delivery.id == uuid.UUID(delivery_id)))
        delivery = result.scalar_one_or_none()
        if not delivery or delivery.status != 'failed':
            return f"Delivery {delivery_id} already success or missing"

        # 2. Check Circuit Breaker
        sub_result = await db.execute(select(Subscriber).where(Subscriber.id == delivery.subscriber_id))
        subscriber = sub_result.scalar_one_or_none()
        if not subscriber or subscriber.status == 'paused':
            return f"Subscriber {subscriber.id if subscriber else 'unknown'} paused, skipping retry"

        # 4. Max Retries check
        if attempt >= subscriber.max_retries:
            delivery.status = 'abandoned'
            redis = ctx['redis']
            dlq_data = {
                "delivery_id": str(delivery.id),
                "subscriber_id": str(subscriber.id),
                "event_id": str(delivery.event_id),
                "abandoned_at": datetime.now(timezone.utc).isoformat()
            }
            await redis.set(f"queue:webhooks:failed:{delivery.id}", json.dumps(dlq_data))
            
            logger.warning("webhook.delivery_abandoned", delivery_id=str(delivery.id), subscriber_id=str(subscriber.id))
            await db.commit()
            return f"Delivery {delivery_id} abandoned after {attempt} attempts"

        # 5. Process Retry
        event_result = await db.execute(select(Event).where(Event.id == delivery.event_id))
        event = event_result.scalar_one_or_none()
        if not event:
            return f"Event {delivery.event_id} missing for delivery {delivery_id}"

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

        start_time = time.perf_counter()
        headers = {
            "X-Webhook-Signature": header_value,
            "X-Webhook-Timestamp": str(ts),
            "X-Webhook-Event": event.event_type,
            "X-Webhook-ID": webhook_id,
            "X-Webhook-Attempt": str(attempt + 1),
            "Content-Type": "application/json",
            "User-Agent": "WebhookService/1.0"
        }

        redis = ctx['redis']
        try:
            async with httpx.AsyncClient(timeout=subscriber.timeout_ms / 1000) as client:
                resp = await client.post(subscriber.callback_url, data=raw_body, headers=headers)
                duration = int((time.perf_counter() - start_time) * 1000)
                
                delivery.http_status = resp.status_code
                delivery.duration_ms = duration
                delivery.attempt_number = attempt + 1
                
                if 200 <= resp.status_code < 300:
                    logger.info("webhook.retry_success", delivery_id=delivery_id, status=resp.status_code, callback_url=subscriber.callback_url)
                    delivery.status = 'success'
                    delivery.delivered_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    await CircuitBreakerService.close_circuit(subscriber.id, redis, db)
                else:
                    logger.warning("webhook.retry_failed", delivery_id=delivery_id, status=resp.status_code, callback_url=subscriber.callback_url)
                    delivery.status = 'failed'
                    delivery.response_body = resp.text[:1000]
                    await handle_retry_failure(ctx, db, redis, subscriber, delivery, attempt)
                    
        except Exception as e:
            delivery.status = 'failed'
            delivery.response_body = str(e)[:1000]
            await handle_retry_failure(ctx, db, redis, subscriber, delivery, attempt)

        await db.commit()
        return f"Retry attempt {attempt + 1} for delivery {delivery_id} finished"

async def handle_retry_failure(ctx, db, redis, subscriber, delivery, attempt):
    await CircuitBreakerService.increment_failure(subscriber.id, redis, db)
    
    # We check if it was paused inside increment_failure, but we still need to enqueue next retry if NOT paused
    result = await db.execute(select(Subscriber.status).where(Subscriber.id == subscriber.id))
    current_status = result.scalar()
    
    if current_status != "paused":
        # Table levels: 1:0s, 2:1s, 3:2s, 4:4s, 5:30s, 6:120s, 7:300s, 8-10:1800s
        # next_attempt is attempt + 1
        next_attempt = attempt + 1
        backoffs = {1: 0, 2: 1, 3: 2, 4: 4, 5: 30, 6: 120, 7: 300, 8: 1800, 9: 1800, 10: 1800}
        delay = backoffs.get(next_attempt, 1800)
        
        await ctx['pool'].enqueue_job(
            "retry_delivery",
            delivery_id=str(delivery.id),
            attempt=next_attempt,
            _defer_by=delay
        )
