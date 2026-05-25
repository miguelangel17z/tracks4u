from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from payment.models import License
from .serializers import LoginSerializer,UserSerializer,UpdateProfileSerializer
from ..service import AuthService, RegisterService, UpdateProfileService
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class loginView(APIView):
    authentication_classes = []  # desactiva autenticación
    permission_classes = []
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
        
            tokens = AuthService.login(password=serializer.validated_data.get("password"),
                                    username=serializer.validated_data.get("username")
                                   )
            return Response(tokens, status=status.HTTP_200_OK)
        
        except ValueError as e:
            return Response({str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self,request):
        return render(request,'registerTemplate.html')

    def post(self,request):
        serializer = UserSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({"error":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        try:

            RegisterService.register(data=serializer.validated_data)
            return Response({"mensaje":"Usuario creado correctamente"}, status=status.HTTP_201_CREATED)


        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


class UpdateProfileView(APIView):
    authentication_classes = [JWTAuthentication]  
    permission_classes = [IsAuthenticated]    
    
    def get(self, request):
        """Obtener información del perfil del usuario"""
        user = request.user
        
        licenses = License.objects.filter(user=user).select_related('track')
        
        licenses_data = []
        for license in licenses:
            licenses_data.append({
                'id': license.id,
                'track_title': license.track.title,
                'track_id': license.track.id,
                'license_type': license.license_type,
                'purchase_date': license.created_at,
                'track_cover': license.track.cover_image.url if license.track.cover_image else None,
                'track_bpm': license.track.bpm,
                'track_genre': license.track.genre,
            })
        
        return Response({
            'username': user.username,
            'email': user.email,
            'licenses': licenses_data,
            'total_licenses': len(licenses_data)
        }, status=status.HTTP_200_OK)
    
    def patch(self,request):
        user = request.user
        serializer = UpdateProfileSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
       
        
        try:
            UpdateProfileService.updateProfile(user,serializer.validated_data)
            return Response(
                {"mensaje": "Usuario actualizado correctamente"},
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        