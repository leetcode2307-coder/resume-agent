import os
import asyncio
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "resume_agent",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(bind=True)
def run_workflow_task(self, job_id: str, request_dict: dict):
    from app.worker_logic import process_job_async
    asyncio.run(process_job_async(job_id, request_dict))
