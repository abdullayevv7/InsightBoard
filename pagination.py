"""
Celery configuration for InsightBoard project.
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("insightboard")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks([
    "apps.reports",
    "apps.alerts",
])

app.conf.beat_schedule = {
    "check-metric-alerts": {
        "task": "apps.alerts.tasks.check_all_active_alerts",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "alerts"},
    },
    "process-scheduled-reports": {
        "task": "apps.reports.tasks.process_scheduled_reports",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "reports"},
    },
    "cleanup-expired-exports": {
        "task": "apps.reports.tasks.cleanup_expired_exports",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "maintenance"},
    },
}

app.conf.task_queues = {
    "default": {"exchange": "default", "routing_key": "default"},
    "alerts": {"exchange": "alerts", "routing_key": "alerts"},
    "reports": {"exchange": "reports", "routing_key": "reports"},
    "datasources": {"exchange": "datasources", "routing_key": "datasources"},
    "maintenance": {"exchange": "maintenance", "routing_key": "maintenance"},
}

app.conf.task_default_queue = "default"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
