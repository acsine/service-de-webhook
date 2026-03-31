from arq.connections import RedisSettings
from app.config.settings import settings
from app.workers.dispatcher import dispatch_event
from app.workers.retry_worker import retry_delivery
from app.workers.refresh_stats import refresh_stats_view
from arq import cron

class WorkerSettings:
    functions = [dispatch_event, retry_delivery, refresh_stats_view]
    cron_jobs = [
        cron(refresh_stats_view, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55})
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 300
