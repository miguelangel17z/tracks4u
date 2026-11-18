import logging
import os
from typing import Optional

from django.core.exceptions import ValidationError
import mutagen
from PIL import Image

logger = logging.getLogger(__name__)

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".opus"}
MAX_AUDIO_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_audio_file(uploaded_file) -> None:
    if not uploaded_file:
        return
    name = getattr(uploaded_file, "name", "") or ""
    _, ext = os.path.splitext(name)
    ext = ext.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValidationError(
            f"Unsupported audio extension '{ext}'. Allowed: {sorted(ALLOWED_AUDIO_EXTENSIONS)}"
        )

    size = getattr(uploaded_file, "size", None)
    if size is not None and size > MAX_AUDIO_SIZE_BYTES:
        raise ValidationError("Audio file size cannot exceed 50 MB.")

    content_type = getattr(uploaded_file, "content_type", None)
    if content_type:
        ct = content_type.lower()
        if not (
            ct.startswith("audio/")
            or ct in ("application/ogg", "application/octet-stream", "video/ogg")
        ):
            raise ValidationError(f"Invalid audio Content-Type: {content_type}")


def validate_image_file(uploaded_file) -> None:
    if not uploaded_file:
        return
    name = getattr(uploaded_file, "name", "") or ""
    _, ext = os.path.splitext(name)
    ext = ext.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported image extension '{ext}'. Allowed: {sorted(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    size = getattr(uploaded_file, "size", None)
    if size is not None and size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError("Image file size cannot exceed 5 MB.")

    try:
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        img.verify()
    except Exception as exc:
        raise ValidationError("Uploaded file is not a valid image.") from exc
    finally:
        if hasattr(uploaded_file, "seek"):
            try:
                uploaded_file.seek(0)
            except Exception:
                pass


def extract_duration_sec(uploaded_file) -> Optional[int]:
    """Extrae la duración en segundos de un archivo de audio usando mutagen."""
    if not uploaded_file:
        return None
    try:
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        audio = mutagen.File(uploaded_file)
        if audio is not None and getattr(audio, "info", None) is not None:
            length = getattr(audio.info, "length", None)
            if length is not None and length > 0:
                return max(1, int(round(float(length))))
        logger.warning(
            "No se pudo determinar duration_sec con mutagen para %s",
            getattr(uploaded_file, "name", "unknown"),
        )
        return None
    except Exception as exc:
        logger.warning(
            "Error leyendo duración con mutagen para %s: %s",
            getattr(uploaded_file, "name", "unknown"),
            exc,
        )
        return None
    finally:
        if hasattr(uploaded_file, "seek"):
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
