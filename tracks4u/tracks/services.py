import logging
from typing import List, Optional

from django.conf import settings
from django.db import transaction

from .infra.notifications.factory import NotificationFactory
from .models import Artist, Genre, Track, TrackGenre

logger = logging.getLogger(__name__)


class TrackCreatorService:
    """Responsable de orquestar la creación de un track."""

    @staticmethod
    def crear_track(
        track: Track,
        genre_ids: Optional[List[int]] = None,
        notificar_admin: bool = True,
    ) -> Track:
        with transaction.atomic():
            if genre_ids is not None:
                genres = list(Genre.objects.filter(id__in=genre_ids))
                if not genres:
                    raise ValueError("A track must have at least one valid genre.")
                TrackGenre.objects.filter(track=track).delete()
                for g in genres:
                    TrackGenre.objects.get_or_create(track=track, genre=g)

            if notificar_admin:
                transaction.on_commit(
                    lambda: TrackNotificationService.notificar_track_subido(track)
                )
        return track


class TrackNotificationService:
    """Responsable de enviar notificaciones relacionadas a tracks."""

    @staticmethod
    def notificar_track_subido(track: Track) -> bool:
        try:
            notificador = NotificationFactory.crear_notificador(
                tipo="email",
                template_type="track_uploaded",
            )
            artist_name = (
                track.artist.stage_name
                if getattr(track, "artist", None)
                else "Unknown Artist"
            )
            genre_names = ", ".join(g.name for g in track.genres.all()) or "Sin género"
            created_str = (
                track.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if track.created_at
                else ""
            )
            contexto = {
                "title": track.title,
                "artist": artist_name,
                "bpm": track.bpm or "N/A",
                "genres": genre_names,
                "created_at": created_str,
            }
            return notificador.enviar(
                destinatario=settings.ADMIN_EMAIL,
                contexto=contexto,
            )
        except Exception as exc:
            logger.error("Error al enviar notificación de track subido: %s", exc)
            return False


class TrackQueryService:
    """Responsable de consultar tracks."""

    @staticmethod
    def obtener_por_id(track_id: int) -> Optional[Track]:
        return (
            Track.objects.filter(id=track_id)
            .select_related("artist")
            .prefetch_related("genres")
            .first()
        )

    @staticmethod
    def listar_disponibles() -> List[Track]:
        return list(
            Track.objects.select_related("artist")
            .prefetch_related("genres")
            .order_by("-created_at")
        )

    @staticmethod
    def listar_todos() -> List[Track]:
        return TrackQueryService.listar_disponibles()
