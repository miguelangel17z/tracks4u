from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from tracks.models import Track
from .services import LicenseService
from tracks.services import TrackQueryService
from .models import User
from .api.serializers import LicenseSerializer


class LicensingView(APIView):

    def get(self,request):
        return render(request,'licensing.html', {"tracks":TrackQueryService.listar_disponibles()})


    def post(self, request):
        data = request.data.copy()
        #data['user'] = request.user.id   # inyectamos user desde la sesión

        # usuario de prubea
        data['user'] = User.objects.first().id

        serializer = LicenseSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            LicenseService.crear_licencia(data=serializer.validated_data)
            return Response("Licencia creada correctamente", status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

            
    

