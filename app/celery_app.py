import os
import asyncio
import ssl
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "resume_agent",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

if REDIS_URL.startswith("rediss://"):
    celery_app.conf.update(
        broker_use_ssl={'ssl_cert_reqs': ssl.CERT_NONE},
        redis_backend_use_ssl={'ssl_cert_reqs': ssl.CERT_NONE}
    )

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_max_tasks_per_child=2,      # Recycle worker after 2 tasks to free memory
    worker_max_memory_per_child=250000 # Recycle if worker memory exceeds ~250MB
)

@celery_app.task(bind=True)
def run_workflow_task(self, job_id: str, request_dict: dict):
    from app.worker_logic import process_job_async
    asyncio.run(process_job_async(job_id, request_dict))
