import os
import uuid


def _extract_ext(filename: str, default_ext: str) -> str:
    _, ext = os.path.splitext(filename or "")
    ext = ext.lstrip(".").lower()
    return ext or default_ext


def track_audio_path(instance, filename: str) -> str:
    """Genera la key relativa en S3 para archivos de audio: audio/<artist_id>/<uuid4>.<ext>."""
    ext = _extract_ext(filename, "mp3")
    artist_id = getattr(instance, "artist_id", None)
    if artist_id is None and getattr(instance, "artist", None) is not None:
        artist_id = instance.artist.pk
    artist_segment = artist_id if artist_id is not None else "unassigned"
    return f"audio/{artist_segment}/{uuid.uuid4().hex}.{ext}"


def track_cover_path(instance, filename: str) -> str:
    """Genera la key relativa en S3 para portadas de tracks: covers/tracks/<uuid4>.<ext>."""
    ext = _extract_ext(filename, "jpg")
    return f"covers/tracks/{uuid.uuid4().hex}.{ext}"


def playlist_cover_path(instance, filename: str) -> str:
    """Genera la key relativa en S3 para portadas de playlists: covers/playlists/<uuid4>.<ext>."""
    ext = _extract_ext(filename, "jpg")
    return f"covers/playlists/{uuid.uuid4().hex}.{ext}"
