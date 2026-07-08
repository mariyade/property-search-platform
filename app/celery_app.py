import os

from celery import Celery

celery_app = Celery(
    "property_search_platform",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=["app.tasks.search_runs"],
)

celery_app.conf.update(
    task_track_started=True,
)
