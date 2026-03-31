import asyncio
from arq import run_worker
from app.workers.settings import WorkerSettings

if __name__ == "__main__":
    run_worker(WorkerSettings)
