from typing import Optional, List
from django.conf import settings
from datetime import datetime

from .models import Track
from .notifications.factory import NotificationFactory


class TrackService:
    """
    Servicio para gestionar operaciones relacionadas con tracks.
    """
    
    @staticmethod
    def crear_track(title: str, audio_file, price: float, bpm: int, 
                   notificar_admin: bool = True) -> Track:
        """
        Crea un nuevo track y opcionalmente notifica al admin.
        """
        track = Track.objects.create(
            title=title,
            audio_file=audio_file,
            price=price,
            bpm=bpm
        )
        
        if notificar_admin:
            TrackService._notificar_track_subido(track)
        
        return track
    
    @staticmethod
    def _notificar_track_subido(track: Track) -> bool:
        """Notifica al admin cuando se sube un nuevo track."""
        try:
            notificador = NotificationFactory.crear_notificador(
                tipo='email',
                template_type='track_uploaded'
            )
            
            contexto = {
                'title': track.title,
                'price': track.price,
                'bpm': track.bpm,
                'created_at': track.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return notificador.enviar(
                destinatario=settings.ADMIN_EMAIL,
                contexto=contexto
            )
            
        except Exception as e:
            print(f"Error al enviar notificación: {e}")
            return False
    
    @staticmethod
    def obtener_track_por_id(track_id: int) -> Optional[Track]:
        """Obtiene un track por su ID."""
        try:
            return Track.objects.get(id=track_id)
        except Track.DoesNotExist:
            return None
    
    @staticmethod
    def listar_tracks_disponibles() -> List[Track]:
        """Lista todos los tracks no vendidos."""
        return list(Track.objects.filter(is_sold=False).order_by('-created_at'))
    
    @staticmethod
    def listar_todos_tracks() -> List[Track]:
        """Lista todos los tracks."""
        return list(Track.objects.all().order_by('-created_at'))