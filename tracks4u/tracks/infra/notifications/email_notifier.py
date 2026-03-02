from django.core.mail import send_mail
from django.conf import settings
from typing import Dict, Any
import logging

from .base import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """
    Notificador que envía emails reales.
    """
    
    def __init__(self, template_type: str):
        self.template_type = template_type
        self.templates = {
            'track_uploaded': {
                'subject': 'Nuevo Track Subido - {title}',
                'message': '''
Hola Admin,

Se ha subido un nuevo track al sistema:

Título: {title}
Precio: ${price}
BPM: {bpm}
Fecha: {created_at}

Saludos,
Sistema Tracks4U
                '''.strip()
            },
            'track_sold': {
                'subject': 'Track Vendido - {title}',
                'message': '''
¡Felicidades!

Tu track "{title}" ha sido vendido.

Comprador: {buyer_username}
Precio: ${price}
Fecha: {purchase_date}

Saludos,
Sistema Tracks4U
                '''.strip()
            },
            'license_created': {
                'subject': 'Nueva Licencia Generada - {track_title}',
                'message': '''
Hola,

Se ha generado una nueva licencia:

Track: {track_title}
Usuario: {user_username}
Tipo de Licencia: {license_type}
Fecha: {created_at}

Saludos,
Sistema Tracks4U
                '''.strip()
            }
        }
    
    def enviar(self, destinatario: str, contexto: Dict[str, Any]) -> bool:
        """
        Envía un email usando el template configurado.
        """
        try:
            template = self.templates.get(self.template_type)
            
            if not template:
                logger.error(f"Template no encontrado: {self.template_type}")
                return False
            
            subject = template['subject'].format(**contexto)
            message = template['message'].format(**contexto)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                fail_silently=False,
            )
            
            logger.info(f"Email enviado a {destinatario} - {self.template_type}")
            return True
            
        except KeyError as e:
            logger.error(f"Falta variable en contexto: {e}")
            return False
        except Exception as e:
            logger.error(f"Error al enviar email: {e}")
            return False