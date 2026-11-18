import json
from typing import List

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from core.validators import extract_duration_sec
from tracks.models import Artist, Genre
from tracks.services import TrackCreatorService, TrackQueryService
from .serializers import ArtistSerializer, GenreSerializer, TrackSerializer


class TrackPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100


def _extract_genre_ids(request) -> List[int]:
    """Extrae genre_ids desde multipart (QueryDict) o JSON."""
    raw = None
    if hasattr(request.data, "getlist"):
        raw = request.data.getlist("genre_ids") or request.data.getlist("genre_ids[]")
    if not raw:
        val = request.data.get("genre_ids")
        if isinstance(val, list):
            raw = val
        elif isinstance(val, str) and val.strip():
            val_str = val.strip()
            if val_str.startswith("["):
                try:
                    raw = json.loads(val_str)
                except Exception:
                    raw = [x.strip() for x in val_str.split(",") if x.strip()]
            else:
                raw = [x.strip() for x in val_str.split(",") if x.strip()]
        elif isinstance(val, int):
            raw = [val]
    result = []
    for item in raw or []:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            pass
    return result


def _extract_mood_tags(request):
    """Extrae mood_tags desde multipart o JSON."""
    if "mood_tags" not in request.data:
        return None
    if hasattr(request.data, "getlist"):
        lst = request.data.getlist("mood_tags")
        if len(lst) == 1 and isinstance(lst[0], str) and "," in lst[0]:
            return [t.strip() for t in lst[0].split(",") if t.strip()]
        if lst and any(str(x).strip() for x in lst):
            return [str(x).strip() for x in lst if str(x).strip()]
        return None
    val = request.data.get("mood_tags")
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str) and val.strip():
        return [t.strip() for t in val.split(",") if t.strip()]
    return None


class GenreListAPIView(APIView):
    """GET /api/genres/ — Catálogo compartido de géneros."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        genres = Genre.objects.all().order_by("name")
        return Response(GenreSerializer(genres, many=True).data, status=status.HTTP_200_OK)


class ArtistDetailAPIView(APIView):
    """GET /api/artists/<int:pk>/ — Perfil público de un artista con sus tracks."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk: int):
        artist = (
            Artist.objects.filter(id=pk)
            .prefetch_related("genres", "tracks__genres", "tracks__artist")
            .first()
        )
        if artist is None:
            return Response({"error": "Artist not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            ArtistSerializer(artist, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class TrackListCreateAPIView(APIView):
    """
    GET /api/tracks/ — Lista y filtra tracks (q, genre, artist, page).
    POST /api/tracks/ — Sube un track (requiere JWT y perfil de artista).
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        return "Bearer"

    def get(self, request):
        q = request.query_params.get("q")
        genre = request.query_params.get("genre")
        artist = request.query_params.get("artist")
        qs = TrackQueryService.filtrar(q=q, genre=genre, artist=artist)

        paginator = TrackPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = TrackSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"error": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        artist = Artist.objects.filter(user=request.user).first()
        if artist is None:
            return Response(
                {"error": "Only users with an artist profile can upload tracks."},
                status=status.HTTP_403_FORBIDDEN,
            )

        genre_ids = _extract_genre_ids(request)
        if not genre_ids:
            return Response(
                {"error": "A track must have at least one genre (genre_ids)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_audio = request.FILES.get("audio_file")
        duration_sec = extract_duration_sec(uploaded_audio) if uploaded_audio else None

        serializer = TrackSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        mood_tags = _extract_mood_tags(request)

        try:
            save_kwargs = {"artist": artist, "duration_sec": duration_sec}
            if mood_tags is not None:
                save_kwargs["mood_tags"] = mood_tags
            track = serializer.save(**save_kwargs)
            TrackCreatorService.crear_track(
                track=track,
                genre_ids=genre_ids,
                artist=artist,
            )
            track = TrackQueryService.obtener_por_id(track.id)
            return Response(
                TrackSerializer(track, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class TrackDetailAPIView(APIView):
    """GET /api/tracks/<int:pk>/ — Detalle de un track."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, pk: int):
        track = TrackQueryService.obtener_por_id(pk)
        if track is None:
            return Response({"error": "Track not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            TrackSerializer(track, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


# Alias de compatibilidad hacia atrás para /api/tracks/crear/
TrackCreateAPIView = TrackListCreateAPIView
TrackListAPIView = TrackListCreateAPIView
