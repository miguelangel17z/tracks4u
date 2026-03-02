from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseNotifier(ABC):
    """
    Clase base abstracta para todos los notificadores.
    """
    
    @abstractmethod
    def enviar(self, destinatario: str, contexto: Dict[str, Any]) -> bool:
        """
        Envía una notificación.
        
        Args:
            destinatario: Email o identificador del destinatario
            contexto: Diccionario con datos para la notificación
            
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        pass

    print("BaseNotifier cargado correctamente")