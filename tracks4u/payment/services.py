# licenses/service.py

from typing import Optional, List
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import License, LicenseBuilder
from tracks.models import Track
from users.models import User


class LicenseService:
    """
    Servicio para gestionar operaciones relacionadas con licencias.
    """
    
    @staticmethod
    def crear_licencia(user: User, track: Track, license_type: str) -> License:
        """
        Crea una nueva licencia usando el LicenseBuilder.
        
        Args:
            user: Usuario que adquiere la licencia
            track: Track asociado a la licencia
            license_type: Tipo de licencia ('basic', 'premium', 'exclusive')
            
        Returns:
            License: Instancia de licencia creada
            
        Raises:
            ValueError: Si hay errores en la validación
        """
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
    
    @staticmethod
    def obtener_licencia_por_id(license_id: int) -> Optional[License]:
        """
        Obtiene una licencia por su ID.
        
        Args:
            license_id: ID de la licencia
            
        Returns:
            License o None si no existe
        """
        try:
            return License.objects.get(id=license_id)
        except License.DoesNotExist:
            return None
    
    @staticmethod
    def obtener_licencias_usuario(user: User) -> List[License]:
        """
        Obtiene todas las licencias de un usuario.
        
        Args:
            user: Usuario
            
        Returns:
            Lista de licencias del usuario
        """
        return list(License.objects.filter(user=user).select_related('track'))
    
    @staticmethod
    def obtener_licencias_track(track: Track) -> List[License]:
        """
        Obtiene todas las licencias asociadas a un track.
        
        Args:
            track: Track
            
        Returns:
            Lista de licencias del track
        """
        return list(License.objects.filter(track=track).select_related('user'))
    
    @staticmethod
    def usuario_tiene_licencia(user: User, track: Track) -> bool:
        """
        Verifica si un usuario ya tiene una licencia para un track específico.
        
        Args:
            user: Usuario
            track: Track
            
        Returns:
            True si el usuario tiene licencia, False en caso contrario
        """
        return License.objects.filter(user=user, track=track).exists()
    
    @staticmethod
    def obtener_licencia_usuario_track(user: User, track: Track) -> Optional[License]:
        """
        Obtiene la licencia de un usuario para un track específico.
        
        Args:
            user: Usuario
            track: Track
            
        Returns:
            License o None si no existe
        """
        try:
            return License.objects.get(user=user, track=track)
        except License.DoesNotExist:
            return None
    
    @staticmethod
    def track_tiene_licencia_exclusiva(track: Track) -> bool:
        """
        Verifica si un track ya tiene una licencia exclusiva.
        
        Args:
            track: Track a verificar
            
        Returns:
            True si existe licencia exclusiva, False en caso contrario
        """
        return License.objects.filter(track=track, license_type='exclusive').exists()
    
    @staticmethod
    def contar_licencias_por_tipo(track: Track) -> dict:
        """
        Cuenta cuántas licencias de cada tipo tiene un track.
        
        Args:
            track: Track
            
        Returns:
            Diccionario con el conteo por tipo de licencia
        """
        licencias = License.objects.filter(track=track)
        
        return {
            'basic': licencias.filter(license_type='basic').count(),
            'premium': licencias.filter(license_type='premium').count(),
            'exclusive': licencias.filter(license_type='exclusive').count(),
            'total': licencias.count()
        }
    
    @staticmethod
    def eliminar_licencia(license_id: int) -> bool:
        """
        Elimina una licencia por su ID.
        
        Args:
            license_id: ID de la licencia a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        try:
            licencia = License.objects.get(id=license_id)
            licencia.delete()
            return True
        except License.DoesNotExist:
            return False
    
    @staticmethod
    def validar_creacion_licencia(user: User, track: Track, license_type: str) -> List[str]:
        """
        Valida si se puede crear una licencia sin crearla.
        
        Args:
            user: Usuario
            track: Track
            license_type: Tipo de licencia
            
        Returns:
            Lista de errores. Lista vacía si no hay errores.
        """
        errores = []
        
        # Verificar si el usuario ya tiene licencia para este track
        if LicenseService.usuario_tiene_licencia(user, track):
            errores.append("El usuario ya tiene una licencia para este track.")
        
        # Si es exclusiva, verificar que no existan otras licencias
        if license_type == 'exclusive':
            if License.objects.filter(track=track).exists():
                errores.append("No se puede crear licencia exclusiva: el track ya tiene licencias.")
        
        # Si el track ya tiene licencia exclusiva, no se pueden crear más
        if LicenseService.track_tiene_licencia_exclusiva(track):
            errores.append("Este track ya tiene una licencia exclusiva.")
        
        # Validar tipo de licencia
        if license_type not in dict(License.LICENSE_TYPES):
            errores.append(f"Tipo de licencia inválido: {license_type}")
        
        return errores