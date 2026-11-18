from __future__ import annotations

import logging
import os
import unicodedata
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import mutagen
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tracks.models import Genre, Track, TrackGenre

logger = logging.getLogger(__name__)

DEFAULT_S3_BUCKET = "tracks4u-datalake-463790652932-us-east-1"
DEFAULT_S3_REGION = "us-east-1"

CONTENT_TYPES: dict[str, str] = {
    ".opus": "audio/ogg",
    ".ogg": "audio/ogg",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

# Mapeo explícito y determinista de las 36 canciones de database/seed.sql (id 1..36)
# hacia los archivos reales en cancionesCovers/tracks4u/.
SEED_TRACKS_MEDIA: list[dict[str, Any]] = [
    {
        "track_id": 1,
        "artist_id": 10,  # Rauw Alejandro
        "title": "2/Catorce",
        "audio_file": "2\u29f8Catorce.opus",
        "cover_file": "2\u29f8Catorce.webp",
        "duration_sec": 206,
        "genres": ["Reggaeton", "R&B"],
        "subgenre": "R&B Urbano",
        "mood_tags": ["romantic", "chill"],
        "bpm": 98,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 2,
        "artist_id": 3,  # Travis Scott
        "title": "4x4",
        "audio_file": "4X4.opus",
        "cover_file": None,
        "duration_sec": 203,
        "genres": ["Hip-Hop", "Trap"],
        "subgenre": "Southern Trap",
        "mood_tags": ["hype", "energetic"],
        "bpm": 140,
        "price": Decimal("1.99"),
        "language": "en",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 3,
        "artist_id": 1,  # Unknown Artist
        "title": "18",
        "audio_file": "18.opus",
        "cover_file": "18.webp",
        "duration_sec": 131,
        "genres": ["Latin Trap", "Reggaeton"],
        "subgenre": "Trap Urbano",
        "mood_tags": ["urban", "night"],
        "bpm": 124,
        "price": Decimal("1.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 4,
        "artist_id": 4,  # Tyler, The Creator
        "title": "327 (feat. Tyler, The Creator & Billie Essco)",
        "audio_file": "327 (feat. Tyler, The Creator & Billie Essco).opus",
        "cover_file": "327.jpg",
        "duration_sec": 349,
        "genres": ["Hip-Hop", "Alternative Hip-Hop", "Jazz"],
        "subgenre": "Jazz Rap",
        "mood_tags": ["chill", "smooth"],
        "bpm": 84,
        "price": Decimal("2.49"),
        "language": "en",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 5,
        "artist_id": 1,  # Unknown Artist
        "title": "444",
        "audio_file": "444.opus",
        "cover_file": "444.webp",
        "duration_sec": 175,
        "genres": ["Latin Trap", "Reggaeton"],
        "subgenre": "Trap Latino",
        "mood_tags": ["dark", "urban"],
        "bpm": 130,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 6,
        "artist_id": 3,  # Travis Scott
        "title": "90210",
        "audio_file": "90210.opus",
        "cover_file": "90210.webp",
        "duration_sec": 339,
        "genres": ["Hip-Hop", "Trap"],
        "subgenre": "Psychedelic Trap",
        "mood_tags": ["atmospheric", "melodic"],
        "bpm": 118,
        "price": Decimal("2.49"),
        "language": "en",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 7,
        "artist_id": 4,  # Tyler, The Creator
        "title": "A BOY IS A GUN*",
        "audio_file": "A BOY IS A GUN\uff0a.opus",
        "cover_file": "IGOR.png",
        "duration_sec": 234,
        "genres": ["Hip-Hop", "Alternative Hip-Hop", "R&B"],
        "subgenre": "Neo-Soul Rap",
        "mood_tags": ["soulful", "melancholic"],
        "bpm": 89,
        "price": Decimal("2.49"),
        "language": "en",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 8,
        "artist_id": 2,  # A$AP Rocky
        "title": "L$D",
        "audio_file": "A$AP Rocky - L$D (Explicit - Official Video).opus",
        "cover_file": "l$d.png",
        "duration_sec": 329,
        "genres": ["Hip-Hop", "Rap"],
        "subgenre": "Experimental Rap",
        "mood_tags": ["psychedelic", "dreamy"],
        "bpm": 120,
        "price": Decimal("2.49"),
        "language": "en",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 9,
        "artist_id": 2,  # A$AP Rocky
        "title": "Praise the Lord (Da Shine) (feat. Skepta)",
        "audio_file": "A$AP Rocky - Praise The Lord (Da Shine) (Official Video) ft. Skepta.opus",
        "cover_file": "PRAISE THE LORD.jpeg",
        "duration_sec": 227,
        "genres": ["Hip-Hop", "Rap", "Grime"],
        "subgenre": "Experimental Rap",
        "mood_tags": ["hype", "confident"],
        "bpm": 80,
        "price": Decimal("2.49"),
        "language": "en",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 10,
        "artist_id": 1,  # Unknown Artist (Mora)
        "title": "AURORA",
        "audio_file": "AURORA.opus",
        "cover_file": "AURORA.webp",
        "duration_sec": 193,
        "genres": ["Reggaeton", "Latin"],
        "subgenre": "Reggaeton Melódico",
        "mood_tags": ["melodic", "night"],
        "bpm": 95,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 11,
        "artist_id": 5,  # Bad Bunny
        "title": "120",
        "audio_file": "BAD BUNNY - 120 \uff5c EL \xdaLTIMO TOUR DEL MUNDO [Visualizer].opus",
        "cover_file": None,
        "duration_sec": 151,
        "genres": ["Latin Trap", "Trap"],
        "subgenre": "Latin Trap",
        "mood_tags": ["melancholic", "chill"],
        "bpm": 120,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 12,
        "artist_id": 5,  # Bad Bunny
        "title": "GRACIAS POR NADA",
        "audio_file": "BAD BUNNY - GRACIAS POR NADA (Visualizer) \uff5c nadie sabe lo que va a pasar ma\xf1ana.opus",
        "cover_file": "BAD BUNNY - GRACIAS POR NADA (Visualizer) \uff5c nadie sabe lo que va a pasar ma\xf1ana.webp",
        "duration_sec": 176,
        "genres": ["Latin Trap", "Reggaeton"],
        "subgenre": "Latin Trap",
        "mood_tags": ["introspective", "urban"],
        "bpm": 136,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 13,
        "artist_id": 5,  # Bad Bunny
        "title": "KLOuFRENS",
        "audio_file": "BAD BUNNY - KLOuFRENS (Visualizer) \uff5c DeB\xcd TiRAR M\xe1S FOToS.opus",
        "cover_file": "BAD BUNNY - KLOuFRENS (Visualizer) \uff5c DeB\xcd TiRAR M\xe1S FOToS.webp",
        "duration_sec": 201,
        "genres": ["Reggaeton", "Latin"],
        "subgenre": "Perreo",
        "mood_tags": ["party", "dance"],
        "bpm": 96,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 14,
        "artist_id": 5,  # Bad Bunny
        "title": "LA DIFÍCIL",
        "audio_file": "BAD BUNNY - LA DIF\xcdCIL \uff5c YHLQMDLG (Video Oficial).opus",
        "cover_file": "BAD BUNNY - LA DIF\xcdCIL \uff5c YHLQMDLG (Video Oficial).webp",
        "duration_sec": 192,
        "genres": ["Reggaeton", "Latin"],
        "subgenre": "Reggaeton Clásico",
        "mood_tags": ["party", "energetic"],
        "bpm": 90,
        "price": Decimal("2.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 15,
        "artist_id": 5,  # Bad Bunny
        "title": "LA MuDANZA",
        "audio_file": "BAD BUNNY - LA MuDANZA (Video Oficial) \uff5c DeB\xcd TiRAR M\xe1S FOToS.opus",
        "cover_file": "BAD BUNNY - LA MuDANZA (Video Oficial) \uff5c DeB\xcd TiRAR M\xe1S FOToS.webp",
        "duration_sec": 215,
        "genres": ["Salsa", "Latin"],
        "subgenre": "Salsa Urbana",
        "mood_tags": ["upbeat", "roots"],
        "bpm": 105,
        "price": Decimal("2.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 16,
        "artist_id": 5,  # Bad Bunny
        "title": "LO QUE LE PASÓ A HAWAii",
        "audio_file": "BAD BUNNY - LO QUE LE PAS\xd3 A HAWAii (Visualizer) \uff5c DeB\xcd TiRAR M\xe1S FOToS.opus",
        "cover_file": "BAD BUNNY - LO QUE LE PAS\xd3 A HAWAii (Visualizer) \uff5c DeB\xcd TiRAR M\xe1S FOToS.webp",
        "duration_sec": 230,
        "genres": ["Latin", "Alternative Hip-Hop"],
        "subgenre": "Jíbaro / Urbano",
        "mood_tags": ["reflective", "acoustic"],
        "bpm": 88,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 17,
        "artist_id": 5,  # Bad Bunny
        "title": "MONACO",
        "audio_file": "BAD BUNNY - MONACO (Official Video) \uff5c nadie sabe lo que va a pasar ma\xf1ana.opus",
        "cover_file": "BAD BUNNY - MONACO (Official Video) \uff5c nadie sabe lo que va a pasar ma\xf1ana.webp",
        "duration_sec": 440,
        "genres": ["Latin Trap", "Hip-Hop"],
        "subgenre": "Orchestral Trap",
        "mood_tags": ["luxury", "confident"],
        "bpm": 139,
        "price": Decimal("2.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 18,
        "artist_id": 5,  # Bad Bunny
        "title": "PIToRRO DE COCO",
        "audio_file": "BAD BUNNY - PIToRRO DE COCO (Video Oficial) \uff5c DeB\xcd TiRAR M\xe1S FOToS.opus",
        "cover_file": "BAD BUNNY - PIToRRO DE COCO (Video Oficial) \uff5c DeB\xcd TiRAR M\xe1S FOToS.webp",
        "duration_sec": 236,
        "genres": ["Latin", "Reggaeton"],
        "subgenre": "Plena / Jíbaro",
        "mood_tags": ["nostalgic", "festive"],
        "bpm": 98,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 19,
        "artist_id": 5,  # Bad Bunny
        "title": "ACHO PR (feat. Arcángel, De La Ghetto, Ñengo Flow)",
        "audio_file": "BAD BUNNY ft. ARC\xc1NGEL, DE LA GHETTO, \xd1ENGO FLOW - ACHO PR (Visualizer) \uff5c nslqvapm.opus",
        "cover_file": None,
        "duration_sec": 360,
        "genres": ["Latin Trap", "Reggaeton"],
        "subgenre": "Malianteo",
        "mood_tags": ["intense", "street"],
        "bpm": 145,
        "price": Decimal("2.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 20,
        "artist_id": 6,  # Bad Gyal
        "title": "BADGYAL",
        "audio_file": "BADGYAL.opus",
        "cover_file": "BADGYAL.webp",
        "duration_sec": 254,
        "genres": ["Reggaeton", "Dancehall"],
        "subgenre": "Urbano Español",
        "mood_tags": ["club", "dance"],
        "bpm": 100,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 21,
        "artist_id": 1,  # Unknown Artist (Saiko)
        "title": "COSAS QUE NO TE DIJE",
        "audio_file": "COSAS QUE NO TE DIJE.opus",
        "cover_file": "COSAS QUE NO TE DIJE.webp",
        "duration_sec": 225,
        "genres": ["Reggaeton", "Pop"],
        "subgenre": "Pop Urbano",
        "mood_tags": ["romantic", "melodic"],
        "bpm": 110,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 22,
        "artist_id": 9,  # Ryan Castro
        "title": "FDSR",
        "audio_file": "FDSR.opus",
        "cover_file": "FDSR.webp",
        "duration_sec": 188,
        "genres": ["Reggaeton", "Latin"],
        "subgenre": "Reggaeton Colombiano",
        "mood_tags": ["party", "melodic"],
        "bpm": 96,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 23,
        "artist_id": 7,  # Feid
        "title": "FUMETEO",
        "audio_file": "Feid - FUMETEO (Official Video).opus",
        "cover_file": "Feid - FUMETEO (Official Video).webp",
        "duration_sec": 141,
        "genres": ["Reggaeton", "Latin"],
        "subgenre": "Perreo",
        "mood_tags": ["energetic", "club"],
        "bpm": 94,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 24,
        "artist_id": 7,  # Feid
        "title": "GODIVA",
        "audio_file": "GODIVA.opus",
        "cover_file": "GODIVA.webp",
        "duration_sec": 219,
        "genres": ["Reggaeton", "Latin"],
        "subgenre": "Reggaeton",
        "mood_tags": ["night", "smooth"],
        "bpm": 92,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 25,
        "artist_id": 1,  # Unknown Artist (Latin Mafia)
        "title": "Julietota",
        "audio_file": "Julietota.opus",
        "cover_file": "Julietota.webp",
        "duration_sec": 212,
        "genres": ["Latin", "Pop", "R&B"],
        "subgenre": "Alt Pop Latino",
        "mood_tags": ["chill", "groove"],
        "bpm": 102,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 26,
        "artist_id": 8,  # Tainy
        "title": "LA BABY",
        "audio_file": "LA BABY - Tainy, Daddy Yankee, Feid, Sech (Official Video).opus",
        "cover_file": "LA BABY - Tainy, Daddy Yankee, Feid, Sech (Official Video).webp",
        "duration_sec": 183,
        "genres": ["Reggaeton", "Latin"],
        "subgenre": "Reggaeton",
        "mood_tags": ["party", "dance"],
        "bpm": 93,
        "price": Decimal("2.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 27,
        "artist_id": 8,  # Tainy
        "title": "MOJABI GHOST (feat. Bad Bunny)",
        "audio_file": "MOJABI GHOST - Tainy, Bad Bunny.opus",
        "cover_file": "MOJABI GHOST - Tainy, Bad Bunny.webp",
        "duration_sec": 234,
        "genres": ["Electronic", "Latin", "Dance"],
        "subgenre": "Synthwave Urbano",
        "mood_tags": ["synth", "night"],
        "bpm": 122,
        "price": Decimal("2.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 28,
        "artist_id": 9,  # Ryan Castro
        "title": "Mujeriego",
        "audio_file": "Mujeriego.opus",
        "cover_file": "Mujeriego.webp",
        "duration_sec": 142,
        "genres": ["Latin", "Salsa", "Reggaeton"],
        "subgenre": "Merengue Urbano",
        "mood_tags": ["festive", "dance"],
        "bpm": 115,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 29,
        "artist_id": 10,  # Rauw Alejandro
        "title": "Nostálgico",
        "audio_file": "Nost\xe1lgico.opus",
        "cover_file": "Nost\xe1lgico.webp",
        "duration_sec": 210,
        "genres": ["Reggaeton", "Dance", "R&B"],
        "subgenre": "UK Garage / Reggaeton",
        "mood_tags": ["groove", "nostalgic"],
        "bpm": 98,
        "price": Decimal("2.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 30,
        "artist_id": 8,  # Tainy
        "title": "PARANORMAL",
        "audio_file": "PARANORMAL.opus",
        "cover_file": "PARANORMAL.webp",
        "duration_sec": 198,
        "genres": ["Reggaeton", "Electronic", "Latin"],
        "subgenre": "Experimental Reggaeton",
        "mood_tags": ["atmospheric", "futuristic"],
        "bpm": 100,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 31,
        "artist_id": 8,  # Tainy
        "title": "PASIEMPRE",
        "audio_file": "PASIEMPRE - Tainy, Arcangel, Myke Towers, Jhayco, Omar Courtz, Arca (Official Visualizer).opus",
        "cover_file": "PASIEMPRE - Tainy, Arcangel, Myke Towers, Jhayco, Omar Courtz, Arca (Official Visualizer).webp",
        "duration_sec": 358,
        "genres": ["Latin Trap", "Reggaeton", "Latin"],
        "subgenre": "Experimental Trap",
        "mood_tags": ["epic", "intense"],
        "bpm": 118,
        "price": Decimal("2.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 32,
        "artist_id": 10,  # Rauw Alejandro
        "title": "AL CALLAO",
        "audio_file": "Rauw Alejandro - AL CALLAO (Visualizer).opus",
        "cover_file": "Rauw Alejandro - AL CALLAO (Visualizer).webp",
        "duration_sec": 243,
        "genres": ["Reggaeton", "R&B"],
        "subgenre": "Reggaeton",
        "mood_tags": ["sensual", "night"],
        "bpm": 92,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 33,
        "artist_id": 10,  # Rauw Alejandro
        "title": "HOY AQUÍ",
        "audio_file": "Rauw Alejandro - HOY AQU\xcd (Visualizer).opus",
        "cover_file": "Rauw Alejandro - HOY AQU\xcd (Visualizer).webp",
        "duration_sec": 188,
        "genres": ["Reggaeton", "Pop", "Electronic"],
        "subgenre": "Synth Reggaeton",
        "mood_tags": ["upbeat", "night"],
        "bpm": 116,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 34,
        "artist_id": 10,  # Rauw Alejandro
        "title": "Espresso Martini (feat. Marconi Impara, Yan Block)",
        "audio_file": "Rauw Alejandro, Marconi Impara, Yan Block - Espresso Martini (Official Lyric Video).opus",
        "cover_file": "Rauw Alejandro, Marconi Impara, Yan Block - Espresso Martini (Official Lyric Video).webp",
        "duration_sec": 191,
        "genres": ["Reggaeton", "Latin Trap"],
        "subgenre": "Trap / Reggaeton",
        "mood_tags": ["club", "smooth"],
        "bpm": 95,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
    {
        "track_id": 35,
        "artist_id": 7,  # Feid
        "title": "REMIX EXCLUSIVO",
        "audio_file": "REMIX EXCLUSIVO.opus",
        "cover_file": "REMIX EXCLUSIVO.webp",
        "duration_sec": 207,
        "genres": ["Reggaeton", "Latin"],
        "subgenre": "Perreo",
        "mood_tags": ["party", "perreo"],
        "bpm": 94,
        "price": Decimal("1.99"),
        "language": "es",
        "track_type": "REMIX",
    },
    {
        "track_id": 36,
        "artist_id": 9,  # Ryan Castro
        "title": "UN TRÍO",
        "audio_file": "Ryan Castro, Peso Pluma, SOG - UN TR\xcdO (Video Oficial).opus",
        "cover_file": "Ryan Castro, Peso Pluma, SOG - UN TR\xcdO (Video Oficial).webp",
        "duration_sec": 168,
        "genres": ["Reggaeton", "Latin", "Regional Mexican"],
        "subgenre": "Reggaeton",
        "mood_tags": ["party", "urban"],
        "bpm": 96,
        "price": Decimal("2.49"),
        "language": "es",
        "track_type": "ORIGINAL",
    },
]


def _normalize_filename(name: str) -> str:
    """Normaliza un nombre de archivo reparando posible mojibake CP437->UTF-8 y aplicando NFC."""
    try:
        repaired = name.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        repaired = name
    return unicodedata.normalize("NFC", repaired)


def build_audio_s3_key(track_id: int, artist_id: int, audio_filename: str = ".opus") -> str:
    """Genera la key S3 determinista para el audio según design.md §4.2."""
    ext = Path(audio_filename).suffix.lstrip(".").lower() or "opus"
    uid = uuid.uuid5(uuid.NAMESPACE_DNS, f"tracks4u-track-{track_id}-audio").hex
    return f"audio/{artist_id}/{uid}.{ext}"


def build_cover_s3_key(track_id: int, cover_filename: str | None) -> str | None:
    """Genera la key S3 determinista para la portada según design.md §4.2."""
    if not cover_filename:
        return None
    ext = Path(cover_filename).suffix.lstrip(".").lower() or "webp"
    uid = uuid.uuid5(uuid.NAMESPACE_DNS, f"tracks4u-track-{track_id}-audio").hex
    return f"covers/tracks/{uid}.{ext}"


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, Decimal)):
        return str(value)
    if isinstance(value, list):
        items = ", ".join(_sql_literal(str(x)) for x in value)
        return f"ARRAY[{items}]::TEXT[]"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


class Command(BaseCommand):
    help = (
        "Sincroniza los 36 archivos .opus y portadas de cancionesCovers/tracks4u/ "
        "con S3 y actualiza las filas 1..36 de track y track_genre en RDS."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--media-dir",
            default=str(Path(settings.BASE_DIR).parent / "cancionesCovers" / "tracks4u"),
            help="Ruta local al directorio cancionesCovers/tracks4u/.",
        )
        parser.add_argument(
            "--bucket",
            default=(
                getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
                or os.environ.get("AWS_STORAGE_BUCKET_NAME")
                or DEFAULT_S3_BUCKET
            ),
            help=f"Nombre del bucket S3 destino (default: {DEFAULT_S3_BUCKET}).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Imprime la tabla de mapeo y verifica archivos locales sin tocar S3 ni RDS.",
        )
        parser.add_argument(
            "--skip-s3",
            action="store_true",
            help="Omite la subida de archivos a S3 y solo actualiza metadatos en RDS.",
        )
        parser.add_argument(
            "--skip-db",
            action="store_true",
            help="Omite la actualización en RDS y solo sube los archivos locales a S3.",
        )
        parser.add_argument(
            "--export-sql",
            dest="export_sql",
            default=None,
            help="Genera un script SQL idempotente (p. ej. database/seed_media_updates.sql).",
        )

    def _index_media_dir(self, media_dir: Path) -> dict[str, Path]:
        if not media_dir.exists() or not media_dir.is_dir():
            raise CommandError(f"No existe el directorio de media local: {media_dir}")
        index: dict[str, Path] = {}
        for entry in media_dir.iterdir():
            if not entry.is_file():
                continue
            index[entry.name] = entry
            index[unicodedata.normalize("NFC", entry.name)] = entry
            index[unicodedata.normalize("NFD", entry.name)] = entry
            index[_normalize_filename(entry.name)] = entry
        return index

    def _resolve_entries(self, media_dir: Path) -> list[dict[str, Any]]:
        file_index = self._index_media_dir(media_dir)
        resolved: list[dict[str, Any]] = []

        for item in SEED_TRACKS_MEDIA:
            track_id = item["track_id"]
            artist_id = item["artist_id"]
            audio_name = item["audio_file"]
            cover_name = item["cover_file"]

            audio_path = (
                file_index.get(audio_name)
                or file_index.get(_normalize_filename(audio_name))
                or file_index.get(unicodedata.normalize("NFC", audio_name))
            )
            if audio_path is None or not audio_path.exists():
                raise CommandError(
                    f"Track {track_id}: no se encontró el archivo de audio '{audio_name}' en {media_dir}"
                )

            cover_path: Path | None = None
            if cover_name:
                cover_path = (
                    file_index.get(cover_name)
                    or file_index.get(_normalize_filename(cover_name))
                    or file_index.get(unicodedata.normalize("NFC", cover_name))
                )
                if cover_path is None or not cover_path.exists():
                    raise CommandError(
                        f"Track {track_id}: no se encontró la portada '{cover_name}' en {media_dir}"
                    )

            duration_sec = item["duration_sec"]
            try:
                mf = mutagen.File(str(audio_path))
                if mf is not None and getattr(mf, "info", None) is not None and mf.info.length:
                    duration_sec = int(round(mf.info.length))
            except Exception as exc:
                logger.warning(
                    "No se pudo leer duración con mutagen para %s: %s", audio_path, exc
                )

            audio_s3_key = build_audio_s3_key(track_id, artist_id, audio_name)
            cover_s3_key = build_cover_s3_key(track_id, cover_name)

            resolved.append(
                {
                    **item,
                    "duration_sec": duration_sec,
                    "audio_path": audio_path,
                    "cover_path": cover_path,
                    "audio_s3_key": audio_s3_key,
                    "cover_s3_key": cover_s3_key,
                }
            )

        return resolved

    def _print_mapping_table(self, entries: list[dict[str, Any]]) -> None:
        header = (
            f"{'ID':>2} | {'Art':>3} | {'Dur(s)':>6} | {'Título':<48} | "
            f"{'Audio S3 Key':<46} | {'Cover S3 Key'}"
        )
        self.stdout.write(header)
        self.stdout.write("-" * len(header))
        for e in entries:
            self.stdout.write(
                f"{e['track_id']:>2} | {e['artist_id']:>3} | {e['duration_sec']:>6} | "
                f"{e['title'][:48]:<48} | {e['audio_s3_key']:<46} | {e['cover_s3_key'] or 'NULL'}"
            )

    def _export_sql_file(self, entries: list[dict[str, Any]], output_path: Path) -> None:
        lines: list[str] = [
            "-- Tracks4U - Actualización idempotente de metadatos, duraciones, géneros y keys S3 (36 tracks)",
            "-- Generado automáticamente por: python manage.py sync_seed_media --export-sql",
            "-- Requiere haber aplicado previamente database/schema.sql y database/seed.sql.",
            "",
            "BEGIN;",
            "",
        ]

        for e in entries:
            tid = e["track_id"]
            lines.append(
                f"-- Track {tid}: {e['title']} ({e['duration_sec']}s)"
            )
            lines.append(
                "UPDATE track SET "
                f"artist_id = {_sql_literal(e['artist_id'])}, "
                f"title = {_sql_literal(e['title'])}, "
                f"subgenre = {_sql_literal(e['subgenre'])}, "
                f"language = {_sql_literal(e['language'])}, "
                f"mood_tags = {_sql_literal(e['mood_tags'])}, "
                f"bpm = {_sql_literal(e['bpm'])}, "
                f"track_type = {_sql_literal(e['track_type'])}, "
                f"price = {_sql_literal(e['price'])}, "
                f"audio_file = {_sql_literal(e['audio_s3_key'])}, "
                f"cover_image = {_sql_literal(e['cover_s3_key'])}, "
                f"duration_sec = {_sql_literal(e['duration_sec'])} "
                f"WHERE id = {tid};"
            )
            genre_literals = ", ".join(_sql_literal(g) for g in e["genres"])
            lines.append(
                "INSERT INTO track_genre (track_id, genre_id) "
                f"SELECT {tid}, g.id FROM genre g WHERE g.name IN ({genre_literals}) "
                "ON CONFLICT (track_id, genre_id) DO NOTHING;"
            )
            lines.append("")

        lines.append("COMMIT;")
        lines.append("")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(f"SQL exportado correctamente en: {output_path}")
        )

    def _upload_to_s3(self, entries: list[dict[str, Any]], bucket: str) -> None:
        import boto3

        region = (
            getattr(settings, "AWS_S3_REGION_NAME", None)
            or os.environ.get("AWS_S3_REGION_NAME")
            or DEFAULT_S3_REGION
        )
        client_kwargs: dict[str, Any] = {"region_name": region}
        access_key = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
        secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
        if access_key and secret_key:
            client_kwargs["aws_access_key_id"] = access_key
            client_kwargs["aws_secret_access_key"] = secret_key

        s3 = boto3.client("s3", **client_kwargs)
        uploaded_audio = 0
        uploaded_covers = 0

        for e in entries:
            audio_path: Path = e["audio_path"]
            audio_ext = audio_path.suffix.lower()
            audio_ct = CONTENT_TYPES.get(audio_ext, "audio/ogg")
            s3.upload_file(
                str(audio_path),
                bucket,
                e["audio_s3_key"],
                ExtraArgs={"ContentType": audio_ct},
            )
            uploaded_audio += 1

            cover_path: Path | None = e["cover_path"]
            if cover_path is not None and e["cover_s3_key"]:
                cover_ext = cover_path.suffix.lower()
                cover_ct = CONTENT_TYPES.get(cover_ext, "image/webp")
                s3.upload_file(
                    str(cover_path),
                    bucket,
                    e["cover_s3_key"],
                    ExtraArgs={"ContentType": cover_ct},
                )
                uploaded_covers += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"S3 ({bucket}): subidos {uploaded_audio} audios y {uploaded_covers} portadas."
            )
        )

    def _update_database(self, entries: list[dict[str, Any]]) -> None:
        updated_tracks = 0
        linked_genres = 0

        with transaction.atomic():
            genre_map = {g.name: g for g in Genre.objects.all()}
            for e in entries:
                track = Track.objects.filter(pk=e["track_id"]).first()
                if track is None:
                    track = Track(id=e["track_id"])
                track.artist_id = e["artist_id"]
                track.title = e["title"]
                track.subgenre = e["subgenre"]
                track.language = e["language"]
                track.mood_tags = e["mood_tags"]
                track.bpm = e["bpm"]
                track.track_type = e["track_type"]
                track.price = e["price"]
                track.audio_file = e["audio_s3_key"]
                track.cover_image = e["cover_s3_key"]
                track.duration_sec = e["duration_sec"]
                track.save()
                updated_tracks += 1

                for gname in e["genres"]:
                    genre_obj = genre_map.get(gname)
                    if genre_obj is None:
                        genre_obj, _ = Genre.objects.get_or_create(name=gname)
                        genre_map[gname] = genre_obj
                    _, created = TrackGenre.objects.get_or_create(
                        track_id=track.id,
                        genre_id=genre_obj.id,
                    )
                    if created:
                        linked_genres += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"RDS: actualizados {updated_tracks} tracks y creados {linked_genres} vínculos en track_genre."
            )
        )

    def handle(self, *args, **options):
        media_dir = Path(options["media_dir"]).resolve()
        entries = self._resolve_entries(media_dir)
        self._print_mapping_table(entries)

        if options.get("export_sql"):
            export_path = Path(options["export_sql"]).resolve()
            self._export_sql_file(entries, export_path)

        if options.get("dry_run"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry-run completado: {len(entries)} canciones verificadas en {media_dir}."
                )
            )
            return

        # Si se invocó únicamente para exportar el SQL sin pedir sincronización activa
        if options.get("export_sql") and not options.get("skip_s3") and not options.get("skip_db"):
            return

        if not options.get("skip_s3"):
            self._upload_to_s3(entries, options["bucket"])

        if not options.get("skip_db"):
            self._update_database(entries)
