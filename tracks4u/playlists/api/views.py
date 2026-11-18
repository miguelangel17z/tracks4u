from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from playlists.api.serializers import (
    PlaylistAddTrackSerializer,
    PlaylistReorderSerializer,
    PlaylistSerializer,
    PlaylistTrackSerializer,
)
from playlists.models import Playlist
from playlists.services import PlaylistService


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100


class PlaylistListCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_authenticate_header(self, request):
        return "Bearer"

    def get(self, request):
        playlists = PlaylistService.listar_propias(request.user)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(playlists, request, view=self)
        serializer = PlaylistSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = PlaylistSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            playlist = PlaylistService.crear_playlist(
                owner=request.user,
                name=serializer.validated_data["name"],
                description=serializer.validated_data.get("description", ""),
                tags=serializer.validated_data.get("tags"),
                is_public=serializer.validated_data.get("is_public", False),
                cover_image=serializer.validated_data.get("cover_image"),
            )
            return Response(
                PlaylistSerializer(playlist, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class PlaylistDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        return "Bearer"

    def get(self, request, pk: int):
        playlist = PlaylistService.obtener_visible(pk, request.user)
        if playlist is None:
            return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            PlaylistSerializer(playlist, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk: int):
        if not request.user or not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        playlist = Playlist.objects.filter(id=pk).first()
        if playlist is None:
            return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
        if playlist.owner_id != request.user.id:
            if not playlist.is_public:
                return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PlaylistSerializer(
            playlist,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        updated = PlaylistService.editar_playlist(
            playlist,
            request.user,
            serializer.validated_data,
        )
        return Response(
            PlaylistSerializer(updated, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk: int):
        if not request.user or not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        playlist = Playlist.objects.filter(id=pk).first()
        if playlist is None:
            return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
        if playlist.owner_id != request.user.id:
            if not playlist.is_public:
                return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        PlaylistService.borrar_playlist(playlist, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlaylistTrackAddAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_authenticate_header(self, request):
        return "Bearer"

    def post(self, request, pk: int):
        playlist = Playlist.objects.filter(id=pk).first()
        if playlist is None:
            return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
        if playlist.owner_id != request.user.id:
            if not playlist.is_public:
                return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PlaylistAddTrackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            entry = PlaylistService.agregar_track(
                playlist=playlist,
                user=request.user,
                track_id=serializer.validated_data["track_id"],
                session_id=request.headers.get("X-Session-Id") or "server",
                device=request.headers.get("X-Device") or "unknown",
                entrypoint=request.headers.get("X-Entrypoint") or "playlist",
            )
            return Response(
                PlaylistTrackSerializer(entry, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class PlaylistTrackRemoveAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_authenticate_header(self, request):
        return "Bearer"

    def delete(self, request, pk: int, track_id: int):
        playlist = Playlist.objects.filter(id=pk).first()
        if playlist is None:
            return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
        if playlist.owner_id != request.user.id:
            if not playlist.is_public:
                return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        try:
            PlaylistService.quitar_track(playlist, request.user, track_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_404_NOT_FOUND)


class PlaylistReorderAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_authenticate_header(self, request):
        return "Bearer"

    def put(self, request, pk: int):
        playlist = Playlist.objects.filter(id=pk).first()
        if playlist is None:
            return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
        if playlist.owner_id != request.user.id:
            if not playlist.is_public:
                return Response({"error": "Playlist not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        serializer = PlaylistReorderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            entries = PlaylistService.reordenar(
                playlist,
                request.user,
                serializer.validated_data["track_ids"],
            )
            return Response(
                PlaylistTrackSerializer(entries, many=True, context={"request": request}).data,
                status=status.HTTP_200_OK,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
