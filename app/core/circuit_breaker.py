import uuid
from datetime import datetime, timezone
import structlog
from sqlalchemy import update
from app.models import Subscriber, AuditLog

logger = structlog.get_logger()

class CircuitBreakerService:
    @staticmethod
    async def increment_failure(subscriber_id: uuid.UUID, redis, db):
        cb_key = f"circuit:{subscriber_id}"
        count = await redis.incr(cb_key)
        await redis.expire(cb_key, 3600)  # Reset TTL on every failure (sliding window)
        
        if count >= 5: # Threshold
            await CircuitBreakerService.open_circuit(subscriber_id, db)

    @staticmethod
    async def open_circuit(subscriber_id: uuid.UUID, db):
        # We need the tenant_id for the audit log
        from sqlalchemy import select
        res = await db.execute(select(Subscriber.tenant_id).where(Subscriber.id == subscriber_id))
        tenant_id = res.scalar()

        await db.execute(
            update(Subscriber)
            .where(Subscriber.id == subscriber_id)
            .values(
                status="paused",
                last_failure_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
        )

        audit_log = AuditLog(
            tenant_id=tenant_id,
            actor="system.worker",
            action="circuit_breaker.opened",
            resource_id=subscriber_id
        )
        db.add(audit_log)
        logger.warning("circuit_breaker.opened", subscriber_id=str(subscriber_id))

    @staticmethod
    async def check_half_open(subscriber_id: uuid.UUID, redis, subscriber_status: str) -> bool:
        if subscriber_status != "paused":
            return False
            
        cb_key = f"circuit:{subscriber_id}"
        exists = await redis.exists(cb_key)
        # If key doesn't exist, it means TTL expired -> HALF_OPEN (tentative test)
        return not exists

    @staticmethod
    async def reset_open(subscriber_id: uuid.UUID, redis):
        # Reset TTL to another 1h for the OPEN state if HALF_OPEN test failed
        cb_key = f"circuit:{subscriber_id}"
        await redis.setex(cb_key, 3600, "5") # Threshold value

    @staticmethod
    async def close_circuit(subscriber_id: uuid.UUID, redis, db):
        from sqlalchemy import select
        res = await db.execute(select(Subscriber.tenant_id).where(Subscriber.id == subscriber_id))
        tenant_id = res.scalar()

        await db.execute(
            update(Subscriber)
            .where(Subscriber.id == subscriber_id)
            .values(status="active", failure_count=0)
        )
        await redis.delete(f"circuit:{subscriber_id}")

        audit_log = AuditLog(
            tenant_id=tenant_id,
            actor="system.worker",
            action="circuit_breaker.closed",
            resource_id=subscriber_id
        )
        db.add(audit_log)
        logger.info("circuit_breaker.closed", subscriber_id=str(subscriber_id))
