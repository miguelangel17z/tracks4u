import os
from celery import Celery
 
# Apunta al settings de tu proyecto Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracks4u.settings")
 
app = Celery("tracks4u")
 
# Lee configuración con prefijo CELERY_ desde settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")
 
# Autodiscover tasks en todas las apps de INSTALLED_APPS
# y en el paquete específico donde está tu tarea:
# tracks.infra.notifications.tasks
app.autodiscover_tasks(["tracks.infra.notifications"])
