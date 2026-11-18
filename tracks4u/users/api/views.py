from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from payment.services import OrderService
from tracks.models import Artist
from ..service import AuthService, RegisterService, UpdateProfileService
from .serializers import LoginSerializer, UpdateProfileSerializer, UserSerializer


class loginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tokens = AuthService.login(
                password=serializer.validated_data.get("password"),
                username=serializer.validated_data.get("username"),
                email=serializer.validated_data.get("email"),
            )
            return Response(tokens, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response(
                {"error": str(exc), "detail": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return render(request, "registerTemplate.html")

    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RegisterService.register(data=serializer.validated_data)
            return Response(
                {"mensaje": "Usuario creado correctamente"},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UpdateProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtiene la información del perfil del usuario y su historial de compras."""
        user = request.user
        purchases = OrderService.obtener_compras_usuario(user)

        purchases_data = []
        for item in purchases:
            track = item.track
            cover_url = None
            if track.cover_image:
                try:
                    cover_url = track.cover_image.url
                except Exception:
                    cover_url = str(track.cover_image)
            genre_names = [g.name for g in track.genres.all()]
            purchases_data.append(
                {
                    "id": item.id,
                    "order_id": item.order_id,
                    "track_id": track.id,
                    "track_title": track.title,
                    "track_artist": track.artist.stage_name if track.artist else None,
                    "track_cover": cover_url,
                    "track_bpm": track.bpm,
                    "track_genres": genre_names,
                    "price_paid": str(item.price_paid),
                    "currency": item.currency,
                    "purchase_date": item.created_at,
                }
            )

        artist_obj = Artist.objects.filter(user=user).prefetch_related("genres").first()
        artist_data = None
        if artist_obj:
            artist_data = {
                "id": artist_obj.id,
                "stage_name": artist_obj.stage_name,
                "bio": artist_obj.bio,
                "country": artist_obj.country,
                "genres": [{"id": g.id, "name": g.name} for g in artist_obj.genres.all()],
            }

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "country": user.country,
                "birth_date": user.birth_date,
                "gender": user.gender,
                "ethnicity": user.ethnicity,
                "is_artist": artist_obj is not None,
                "artist": artist_data,
                "purchases": purchases_data,
                "total_purchases": len(purchases_data),
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        user = request.user
        serializer = UpdateProfileSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            UpdateProfileService.updateProfile(user, serializer.validated_data)
            return Response(
                {"mensaje": "Usuario actualizado correctamente"},
                status=status.HTTP_200_OK,
            )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
