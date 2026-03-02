from typing import Optional
from django.conf import settings

from .base import BaseNotifier
from .email_notifier import EmailNotifier
from .mock_notifier import MockEmailNotifier


class NotificationFactory:
    """
    Factory para crear diferentes tipos de notificadores.
    Cambia entre MOCK y REAL según variable de entorno NOTIFICATION_MODE.
    """
    
    @staticmethod
    def crear_notificador(tipo: str, template_type: str) -> Optional[BaseNotifier]:
        """
        Crea un notificador según el tipo y modo configurado.
        """
        mode = settings.NOTIFICATION_MODE
        
        if tipo == 'email':
            if mode == 'MOCK':
                print(f"Usando notificador MOCK para {template_type}")
                return MockEmailNotifier(template_type)
            elif mode == 'REAL':
                print(f"Usando notificador REAL para {template_type}")
                return EmailNotifier(template_type)
            else:
                raise ValueError(f"Modo de notificación no válido: {mode}")
        
        raise ValueError(f"Tipo de notificador no válido: {tipo}")