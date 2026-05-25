from django.conf import settings

SISTEMA_API_BASE_URL = getattr(
    settings,
    "SISTEMA_API_BASE_URL",
    "http://44.198.244.207/api/v1"
)

SISTEMA_API_TIMEOUT = getattr(
    settings,
    "SISTEMA_API_TIMEOUT",
    10
)