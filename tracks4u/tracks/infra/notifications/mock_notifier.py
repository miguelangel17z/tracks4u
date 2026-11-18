import logging
from typing import Any, Dict

from .base import BaseNotifier

logger = logging.getLogger(__name__)


class MockEmailNotifier(BaseNotifier):
    """Notificador Mock que simula el envío de emails para testing y desarrollo."""

    def __init__(self, template_type: str):
        self.template_type = template_type

    def enviar(self, destinatario: str, contexto: Dict[str, Any]) -> bool:
        """Simula el envío de un email registrándolo mediante logging."""
        logger.info(
            "[MOCK EMAIL] template=%s keys=%s",
            self.template_type,
            sorted(contexto.keys()),
        )
        return True
