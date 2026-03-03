from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TrackSerializer
from tracks.services import TrackCreatorService, TrackQueryService


class TrackCreateAPIView(APIView):

    def post(self, request):
        serializer = TrackSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        track = serializer.save()                  # APIView sabe de DRF → hace el save()
        TrackCreatorService.crear_track(track)     # Service recibe Track puro

        return Response(
            TrackSerializer(track).data,
            status=status.HTTP_201_CREATED
        )


class TrackListAPIView(APIView):

    def get(self, request):
        tracks = TrackQueryService.listar_todos()
        serializer = TrackSerializer(tracks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)