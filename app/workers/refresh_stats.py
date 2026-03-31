import structlog
from app.common.db import AsyncSessionLocal
from sqlalchemy import text

logger = structlog.get_logger()

async def refresh_stats_view(ctx):
    """
    Refresh the delivery_stats_hourly materialized view concurrently.
    This does not block reads during the refresh.
    """
    logger.info("refreshing_stats_view")
    async with AsyncSessionLocal() as db:
        try:
            await db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY delivery_stats_hourly"))
            await db.commit()
            logger.info("stats_view_refreshed")
        except Exception as e:
            logger.error("stats_view_refresh_failed", error=str(e))
