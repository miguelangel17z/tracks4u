
from typing import Optional, List
from django.db import transaction
from django.core.exceptions import ValidationError

from .builders import LicenseBuilder
from .models import License
from tracks.models import Track
from users.models import User


class LicenseService:
    """
    Servicio para gestionar operaciones relacionadas con licencias.
    """
    
    @staticmethod
    #        Crea una nueva licencia usando el LicenseBuilder.

    def crear_licencia(user: User, track: Track, license_type: str) -> License:
        try:
            with transaction.atomic():
                licencia = (LicenseBuilder()
                    .para_user(user)
                    .para_track(track)
                    .para_license_type(license_type)
                    .construir())
                
                return licencia
        except ValueError as e:
            raise ValueError(f"Error al crear licencia: {str(e)}")
    
    
    #Obtiene todas las licencias de un usuario.
    @staticmethod
    def obtener_licencias_usuario(user: User) -> List[License]:

        return list(License.objects.filter(user=user).select_related('track'))
    
    

    
   
        
