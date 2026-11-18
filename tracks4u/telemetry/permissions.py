import hmac

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class IsTelemetryDrainClient(BasePermission):
    """
    Autentica y autoriza al conector de drenaje mediante Authorization: Bearer <TELEMETRY_DRAIN_TOKEN>.
    Usa hmac.compare_digest para comparación en tiempo constante.
    Si TELEMETRY_DRAIN_TOKEN está vacío en settings, deniega siempre con 401.
    """

    def has_permission(self, request, view) -> bool:
        expected_token = getattr(settings, "TELEMETRY_DRAIN_TOKEN", "") or ""
        if not expected_token:
            raise AuthenticationFailed("Drain token is not configured.")

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Missing or invalid Authorization Bearer header.")

        provided_token = auth_header[len("Bearer ") :].strip()
        if not provided_token:
            raise AuthenticationFailed("Empty bearer token.")

        if not hmac.compare_digest(
            provided_token.encode("utf-8"),
            expected_token.encode("utf-8"),
        ):
            raise AuthenticationFailed("Invalid drain token.")

        return True
