import logging
from typing import Optional

from django.conf import settings

from .base import BaseNotifier
from .email_notifier import EmailNotifier
from .mock_notifier import MockEmailNotifier

logger = logging.getLogger(__name__)


class NotificationFactory:
    """
    Factory para crear diferentes tipos de notificadores.
    Cambia entre MOCK y REAL según variable de entorno NOTIFICATION_MODE.
    """

    @staticmethod
    def crear_notificador(tipo: str, template_type: str) -> Optional[BaseNotifier]:
        """Crea un notificador según el tipo y modo configurado."""
        mode = settings.NOTIFICATION_MODE

        if tipo == "email":
            if mode == "MOCK":
                logger.debug("Usando notificador MOCK para %s", template_type)
                return MockEmailNotifier(template_type)
            elif mode == "REAL":
                logger.debug("Usando notificador REAL para %s", template_type)
                return EmailNotifier(template_type)
            else:
                raise ValueError(f"Modo de notificación no válido: {mode}")

        raise ValueError(f"Tipo de notificador no válido: {tipo}")
