from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services import LicenseService
from ..api.serializers import LicenseSerializer


class LicensingView(APIView):


    def post(self, request):
        data = request.data.copy()

        serializer = LicenseSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            LicenseService.crear_licencia(data=serializer.validated_data)
            return Response("Licencia creada correctamente", status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

            
    

