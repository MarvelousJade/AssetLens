from celery import Celery

from .config import settings

celery = Celery("assetlens", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_prefetch_multiplier=1,
)
celery.autodiscover_tasks(["app"])
