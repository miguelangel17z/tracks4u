from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .api.serializers import LoginSerializer,UserSerializer,UpdateProfileSerializer
from .service import AuthService, RegisterService, UpdateProfileService
from django.shortcuts import render
from .models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class HomeView(APIView):
    authentication_classes = []  # desactiva autenticación

    def get(self,request):
        return render(request,'home.html')


class loginView(APIView):
    authentication_classes = []  # desactiva autenticación
    permission_classes = []

    def get(self,request):
        return render(request,'loginTemplate.html')
    
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


@method_decorator(login_required, name='dispatch')   
class UpdateProfileView(APIView):
    

    def get(self, request):

        # usuario de prubea
        user = User.objects.first()

        

        return render(request, 'UpdateProfileTemplate.html', {
    'username': user.username,
    'email': user.email,
})
        
      
    
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
        


    








