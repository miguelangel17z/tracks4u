from typing import Optional, List
from django.conf import settings
from .models import Track
from .infra.notifications.factory import NotificationFactory


class TrackCreatorService:
    """Responsable de orquestar la creación de un track."""

    @staticmethod
    def crear_track(track: Track, notificar_admin: bool = True) -> Track:
        if notificar_admin:
            TrackNotificationService.notificar_track_subido(track)
        return track


class TrackNotificationService:
    """Responsable de enviar notificaciones relacionadas a tracks."""

    @staticmethod
    def notificar_track_subido(track: Track) -> bool:
        try:
            notificador = NotificationFactory.crear_notificador(
                tipo="email",
                template_type="track_uploaded"
            )
            contexto = {
                "title": track.title,
                "price": track.price,
                "bpm": track.bpm,
                "created_at": track.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return notificador.enviar(
                destinatario=settings.ADMIN_EMAIL,
                contexto=contexto
            )
        except Exception as e:
            print(f"Error al enviar notificación: {e}")
            return False


class TrackQueryService:
    """Responsable de consultar tracks."""

    @staticmethod
    def obtener_por_id(track_id: int) -> Optional[Track]:
        try:
            return Track.objects.get(id=track_id)
        except Track.DoesNotExist:
            return None

    @staticmethod
    def listar_disponibles() -> List[Track]:
        return list(Track.objects.filter(is_sold=False).order_by('-created_at'))

    @staticmethod
    def listar_todos() -> List[Track]:
        return list(Track.objects.all().order_by('-created_at'))