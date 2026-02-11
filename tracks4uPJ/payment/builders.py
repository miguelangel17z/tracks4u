from tracks.models import Track  
from users.models import User
from .models import License

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
            return self
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

