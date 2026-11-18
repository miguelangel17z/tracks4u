from typing import List, Optional

from django.db import transaction
from django.db.models import Max

from playlists.models import Playlist, PlaylistTrack
from telemetry.services import emit_event
from tracks.models import Track
from users.models import User


class PlaylistService:
    """Servicio de dominio para gestión de playlists, tracks y emisión de telemetría."""

    @staticmethod
    def _assert_owner(playlist: Playlist, user: User) -> None:
        if user is None or not getattr(user, "is_authenticated", False) or playlist.owner_id != user.id:
            raise PermissionError("You do not have permission to modify this playlist.")

    @staticmethod
    def listar_propias(user: User) -> List[Playlist]:
        return list(
            Playlist.objects.filter(owner=user)
            .prefetch_related("playlist_tracks__track__artist", "playlist_tracks__track__genres")
            .order_by("-created_at")
        )

    @staticmethod
    def crear_playlist(
        owner: User,
        name: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        is_public: bool = False,
        cover_image=None,
    ) -> Playlist:
        if not name or not name.strip():
            raise ValueError("Playlist name is required.")
        return Playlist.objects.create(
            owner=owner,
            name=name.strip(),
            description=description or "",
            tags=tags if tags else None,
            is_public=bool(is_public),
            cover_image=cover_image,
        )

    @staticmethod
    def obtener_visible(playlist_id: int, user: Optional[User] = None) -> Optional[Playlist]:
        playlist = (
            Playlist.objects.filter(id=playlist_id)
            .select_related("owner")
            .prefetch_related("playlist_tracks__track__artist", "playlist_tracks__track__genres")
            .first()
        )
        if playlist is None:
            return None
        is_owner = (
            user is not None
            and getattr(user, "is_authenticated", False)
            and playlist.owner_id == user.id
        )
        if not playlist.is_public and not is_owner:
            return None
        return playlist

    @staticmethod
    def editar_playlist(playlist: Playlist, user: User, data: dict) -> Playlist:
        PlaylistService._assert_owner(playlist, user)
        for field in ("name", "description", "tags", "is_public", "cover_image"):
            if field in data:
                setattr(playlist, field, data[field])
        playlist.save()
        return playlist

    @staticmethod
    def borrar_playlist(playlist: Playlist, user: User) -> None:
        PlaylistService._assert_owner(playlist, user)
        playlist.delete()

    @staticmethod
    def agregar_track(
        playlist: Playlist,
        user: User,
        track_id: int,
        session_id: str = "server",
        device: str = "unknown",
        entrypoint: str = "playlist",
    ) -> PlaylistTrack:
        PlaylistService._assert_owner(playlist, user)

        with transaction.atomic():
            track = Track.objects.filter(id=track_id).first()
            if track is None:
                raise ValueError("Track not found.")

            if PlaylistTrack.objects.filter(playlist=playlist, track=track).exists():
                raise ValueError("Track is already in this playlist.")

            max_pos = (
                PlaylistTrack.objects.filter(playlist=playlist).aggregate(
                    max_p=Max("position")
                )["max_p"]
                or 0
            )
            position = max_pos + 1

            entry = PlaylistTrack.objects.create(
                playlist=playlist,
                track=track,
                position=position,
            )

            emit_event(
                "playlist_add",
                user=user,
                session_id=(session_id or "server")[:64],
                device=device or "unknown",
                entrypoint=entrypoint or "playlist",
                payload={
                    "playlist_id": playlist.id,
                    "track_id": track.id,
                    "position": position,
                },
            )
            return entry

    @staticmethod
    def quitar_track(playlist: Playlist, user: User, track_id: int) -> None:
        PlaylistService._assert_owner(playlist, user)

        with transaction.atomic():
            entry = PlaylistTrack.objects.filter(
                playlist=playlist,
                track_id=track_id,
            ).first()
            if entry is None:
                raise ValueError("Track is not in this playlist.")

            entry.delete()

            remaining = list(
                PlaylistTrack.objects.filter(playlist=playlist).order_by("position", "id")
            )
            for idx, item in enumerate(remaining, start=1):
                if item.position != idx:
                    item.position = idx
                    item.save(update_fields=["position", "updated_at"])

    @staticmethod
    def reordenar(playlist: Playlist, user: User, track_ids: List[int]) -> List[PlaylistTrack]:
        PlaylistService._assert_owner(playlist, user)

        if not isinstance(track_ids, list) or len(track_ids) != len(set(track_ids)):
            raise ValueError("track_ids must be a list of unique track IDs.")

        with transaction.atomic():
            entries = list(PlaylistTrack.objects.filter(playlist=playlist))
            current_ids = {e.track_id for e in entries}
            if set(track_ids) != current_ids:
                raise ValueError(
                    "track_ids must contain the exact set of tracks currently in the playlist."
                )

            by_track_id = {e.track_id: e for e in entries}
            ordered = []
            for idx, tid in enumerate(track_ids, start=1):
                entry = by_track_id[tid]
                if entry.position != idx:
                    entry.position = idx
                    entry.save(update_fields=["position", "updated_at"])
                ordered.append(entry)
            return ordered
