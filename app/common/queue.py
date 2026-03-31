from arq import create_pool
from arq.connections import RedisSettings
from app.config.settings import settings

_arq_pool = None

async def get_arq_pool():
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    return _arq_pool

async def enqueue_job(function_name: str, **kwargs):
    pool = await get_arq_pool()
    await pool.enqueue_job(function_name, **kwargs)
