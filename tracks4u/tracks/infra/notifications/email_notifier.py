import logging
from typing import Any, Dict

from django.conf import settings
from django.core.mail import send_mail

from .base import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """Notificador que envía emails reales."""

    def __init__(self, template_type: str):
        self.template_type = template_type
        self.templates = {
            "track_uploaded": {
                "subject": "Nuevo Track Subido - {title}",
                "message": """
Hola Admin,

Se ha subido un nuevo track al sistema:

Título: {title}
Artista: {artist}
BPM: {bpm}
Géneros: {genres}
Fecha: {created_at}

Saludos,
Sistema Tracks4U
                """.strip(),
            },
            "track_sold": {
                "subject": "Track Vendido - {title}",
                "message": """
¡Felicidades!

Tu track "{title}" ha sido vendido.

Comprador: {buyer_username}
Fecha: {purchase_date}

Saludos,
Sistema Tracks4U
                """.strip(),
            },
            "order_completed": {
                "subject": "Orden Completada #{order_id}",
                "message": """
Hola {user_username},

Tu compra se ha procesado exitosamente:

Orden: #{order_id}
Canciones: {items}
Total pagado: {total_amount} {currency}
Fecha: {created_at}

Saludos,
Sistema Tracks4U
                """.strip(),
            },
        }

    def enviar(self, destinatario: str, contexto: Dict[str, Any]) -> bool:
        """Envía un email usando el template configurado."""
        try:
            template = self.templates.get(self.template_type)

            if not template:
                logger.error("Template no encontrado: %s", self.template_type)
                return False

            subject = template["subject"].format(**contexto)
            message = template["message"].format(**contexto)

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                fail_silently=False,
            )

            logger.info("Email enviado (%s)", self.template_type)
            return True

        except KeyError as exc:
            logger.error("Falta variable en contexto de email (%s): %s", self.template_type, exc)
            return False
        except Exception as exc:
            logger.error("Error al enviar email (%s): %s", self.template_type, exc)
            return False
