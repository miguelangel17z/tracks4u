from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseNotifier(ABC):
    """Clase base abstracta para todos los notificadores."""

    @abstractmethod
    def enviar(self, destinatario: str, contexto: Dict[str, Any]) -> bool:
        """Envía una notificación."""
        pass
