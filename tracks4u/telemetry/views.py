from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .permissions import IsTelemetryDrainClient
from .serializers import EventAckSerializer
from .services import ack, drain, ingest_events


class EventIngestView(APIView):
    """POST /api/events/ — Ingesta de eventos de comportamiento desde el front."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get_authenticate_header(self, request):
        return "Bearer"

    def post(self, request):
        data = request.data
        if not isinstance(data, dict):
            return Response(
                {"error": "Request body must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "events" in data:
            events_list = data.get("events")
            if not isinstance(events_list, list) or len(events_list) == 0:
                return Response(
                    {"error": "'events' must be a non-empty list."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if len(events_list) > 100:
                return Response(
                    {"error": "Batch size cannot exceed 100 events."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif "event_type" in data or "event_id" in data:
            events_list = [data]
        else:
            return Response(
                {"error": "Invalid event payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = ingest_events(events=events_list, user=request.user)
        return Response(result, status=status.HTTP_202_ACCEPTED)


class EventDrainView(APIView):
    """GET /api/events/drain/?since=<id>&limit=<n> — Drenaje del outbox hacia Kafka."""

    authentication_classes = []
    permission_classes = [IsTelemetryDrainClient]

    def get_authenticate_header(self, request):
        return "Bearer"

    def get(self, request):
        raw_since = request.query_params.get("since", "0")
        raw_limit = request.query_params.get("limit", "500")

        try:
            since = int(raw_since)
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return Response(
                {"error": "'since' and 'limit' must be valid integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if since < 0 or limit < 1:
            return Response(
                {"error": "'since' must be >= 0 and 'limit' must be >= 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_limit = int(getattr(settings, "TELEMETRY_DRAIN_MAX_LIMIT", 1000))
        effective_limit = min(limit, max_limit)

        result = drain(since=since, limit=effective_limit)
        return Response(result, status=status.HTTP_200_OK)


class EventAckView(APIView):
    """POST /api/events/ack/ — Confirmación de entrega del conector de Kafka."""

    authentication_classes = []
    permission_classes = [IsTelemetryDrainClient]

    def get_authenticate_header(self, request):
        return "Bearer"

    def post(self, request):
        serializer = EventAckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        acked_count = ack(last_id=serializer.validated_data["last_id"])
        return Response({"acked": acked_count}, status=status.HTTP_200_OK)
