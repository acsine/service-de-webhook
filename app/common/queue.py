import os
from arq import create_pool
from arq.connections import RedisSettings
from app.config.settings import settings

_arq_pool = None

async def get_arq_pool():
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    return _arq_pool

async def enqueue_job(function_name: str, background_tasks=None, **kwargs):
    # VERCEL/Serverless Fallback
    if background_tasks:
        if function_name == "dispatch_event":
            from app.workers.dispatcher import dispatch_event
            from app.common.redis import get_redis
            
            # Mock ctx for serverless
            # Note: We use a simple dict as context
            from app.common.redis import get_redis
            redis = get_redis()
            ctx = {'redis': redis, 'pool': await get_arq_pool()}
            
            background_tasks.add_task(dispatch_event, ctx, **kwargs)
            return

    # Standard arq queueing
    pool = await get_arq_pool()
    await pool.enqueue_job(function_name, **kwargs)
