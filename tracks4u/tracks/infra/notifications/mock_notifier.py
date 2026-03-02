from typing import Dict, Any
import logging

from .base import BaseNotifier

logger = logging.getLogger(__name__)


class MockEmailNotifier(BaseNotifier):
    """
    Notificador Mock que simula el envío de emails (para testing/desarrollo).
    """
    
    def __init__(self, template_type: str):
        self.template_type = template_type
    
    def enviar(self, destinatario: str, contexto: Dict[str, Any]) -> bool:
        """
        Simula el envío de un email mostrando en consola.
        """
        print("=" * 60)
        print("MOCK EMAIL NOTIFICATION")
        print("=" * 60)
        print(f"Para: {destinatario}")
        print(f"Tipo: {self.template_type}")
        print(f"Contexto: {contexto}")
        print("=" * 60)
        
        logger.info(f"[MOCK] Email simulado a {destinatario} - {self.template_type}")
        return True