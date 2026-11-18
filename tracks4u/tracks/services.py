import logging
from typing import List, Optional

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from core.validators import extract_duration_sec
from .infra.notifications.factory import NotificationFactory
from .models import Artist, Genre, Track, TrackGenre

logger = logging.getLogger(__name__)


class TrackCreatorService:
    """Responsable de orquestar la creación de un track por un artista."""

    @staticmethod
    def crear_track(
        track: Track,
        genre_ids: Optional[List[int]] = None,
        artist: Optional[Artist] = None,
        uploaded_audio=None,
        notificar_admin: bool = True,
    ) -> Track:
        with transaction.atomic():
            if artist is not None:
                track.artist = artist

            if uploaded_audio is not None and track.duration_sec is None:
                track.duration_sec = extract_duration_sec(uploaded_audio)

            if genre_ids is not None:
                genres = list(Genre.objects.filter(id__in=genre_ids))
                if not genres:
                    raise ValueError("A track must have at least one valid genre.")
                if track.pk is None:
                    track.save()
                TrackGenre.objects.filter(track=track).delete()
                for g in genres:
                    TrackGenre.objects.get_or_create(track=track, genre=g)
            elif track.pk is None:
                track.save()
            else:
                track.save()

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
    """Responsable de consultar y filtrar tracks."""

    @staticmethod
    def obtener_por_id(track_id: int) -> Optional[Track]:
        return (
            Track.objects.filter(id=track_id)
            .select_related("artist")
            .prefetch_related("genres")
            .first()
        )

    @staticmethod
    def filtrar(
        q: Optional[str] = None,
        genre: Optional[str] = None,
        artist: Optional[str] = None,
    ):
        qs = (
            Track.objects.select_related("artist")
            .prefetch_related("genres")
            .order_by("-created_at", "-id")
        )
        if q and q.strip():
            term = q.strip()
            qs = qs.filter(
                Q(title__icontains=term)
                | Q(subgenre__icontains=term)
                | Q(artist__stage_name__icontains=term)
            )
        if genre and str(genre).strip():
            g_val = str(genre).strip()
            if g_val.isdigit():
                qs = qs.filter(genres__id=int(g_val))
            else:
                qs = qs.filter(genres__name__iexact=g_val)
        if artist and str(artist).strip():
            a_val = str(artist).strip()
            if a_val.isdigit():
                qs = qs.filter(artist_id=int(a_val))
            else:
                qs = qs.filter(artist__stage_name__icontains=a_val)
        return qs.distinct()

    @staticmethod
    def listar_disponibles() -> List[Track]:
        return list(TrackQueryService.filtrar())

    @staticmethod
    def listar_todos() -> List[Track]:
        return TrackQueryService.listar_disponibles()
