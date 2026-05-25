import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,   # reintenta cada 60s si falla
    name="notifications.send_email_task",
)
def send_email_task(self, template_type: str, destinatario: str, contexto: dict):
    """
    Task Celery: envía un email en background usando NotificationFactory.

    Args:
        template_type:  'track_uploaded' | 'track_sold' | 'license_created'
        destinatario:   email del destinatario
        contexto:       dict con las variables del template
    """
    from .factory import NotificationFactory   # import local para evitar ciclos

    try:
        notificador = NotificationFactory.crear_notificador(
            tipo="email",
            template_type=template_type,
        )
        resultado = notificador.enviar(destinatario=destinatario, contexto=contexto)

        if not resultado:
            raise ValueError(f"El notificador retornó False para {template_type}")

        logger.info(f"[CELERY] Email '{template_type}' enviado a {destinatario}")
        return {"status": "ok", "template": template_type, "destinatario": destinatario}

    except Exception as exc:
        logger.error(f"[CELERY] Error en send_email_task: {exc}. Reintentando...")
        raise self.retry(exc=exc)