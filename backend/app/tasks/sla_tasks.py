from app.celery_app import celery_app
from app.services.sla_worker import check_sla_breaches


@celery_app.task(name="app.tasks.sla_tasks.check_sla_breaches_task")
def check_sla_breaches_task() -> int:
    return check_sla_breaches()