from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .api.serializers import LoginSerializer,UserSerializer
from .service import AuthService, RegisterService
from django.shortcuts import render


class loginView(APIView):
    authentication_classes = []  # desactiva autenticación

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
            return Response({"error":"Rellenar los datos correctamente"},status=status.HTTP_400_BAD_REQUEST)
        RegisterService.register(data=serializer.validated_data)
        return Response({"mensaje":"Usuario creado correctamente"}, status=status.HTTP_201_CREATED)







