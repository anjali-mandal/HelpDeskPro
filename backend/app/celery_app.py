import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
celery_app = Celery("helpdeskpro", broker=redis_url, backend=redis_url)
celery_app.conf.update(
    timezone="UTC",
    beat_schedule={
        "check-sla-breaches": {
            "task": "app.tasks.sla_tasks.check_sla_breaches_task",
            "schedule": 60.0,
        }
    },
)