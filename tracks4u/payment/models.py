from django.db import models
from tracks.models import Track  
from users.models import User

class License(models.Model):
    LICENSE_TYPES = [
        ('basic', 'Licencia Básica'),
        ('premium', 'Licencia Premium'),
        ('exclusive', 'Licencia Exclusiva'),
    ]
    
    license_type = models.CharField(
        max_length=20,
        choices=LICENSE_TYPES,
        default='basic'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE,     null=True,
    blank=True)
    track = models.ForeignKey(Track, on_delete=models.PROTECT, null=True,
    blank=True)

class LicenseBuilder():
    def __init__(self):
        self.license_data = {}  # Acumula datos temporalmente
        self.errores = []
    
    def para_track(self, track:Track):
        self.license_data['track'] = track
        return self
    
    def para_user(self, user:User):
        self.license_data['user'] = user
        return self
    
    def para_license_type(self, license_type):
        if license_type not in dict(License.LICENSE_TYPES):
            self.errores.append(f"Tipo de licencia inválido: {license_type}")
        else:
            self.license_data['license_type'] = license_type
        return self
    
    def validar(self):
        self.errores = []  # actualizamos lista de errores

        if 'track' not in self.license_data:
            self.errores.append("Falta la pista.")
        elif not isinstance(self.license_data['track'], Track):
            self.errores.append("Track inválido.")

        if 'user' not in self.license_data:
            self.errores.append("Falta el usuario.")
        elif not isinstance(self.license_data['user'], User):
            self.errores.append("Usuario inválido.")

        if 'license_type' not in self.license_data:
            self.errores.append("Falta el tipo de licencia.")

    def construir(self):
        self.validar()
        if self.errores:
            raise ValueError(f"Errores en la construcción de la licencia: {self.errores}")
        
        return License.objects.create(**self.license_data)



    

