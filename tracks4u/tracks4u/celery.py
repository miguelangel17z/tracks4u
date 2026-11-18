import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracks4u.settings")

app = Celery("tracks4u")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks en todas las apps de INSTALLED_APPS y en tracks.infra.notifications
app.autodiscover_tasks()
app.autodiscover_tasks(["tracks.infra.notifications"])
