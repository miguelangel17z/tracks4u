from django.db import models
from tracks.models import Track  

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

class Purchase(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.PROTECT)
    license = models.ForeignKey(License, on_delete=models.PROTECT) #No puedes borrar una License si hay Purchases usándola
    price = models.DecimalField(max_digits=8, decimal_places=2)
    purchased_at = models.DateTimeField(auto_now_add=True)

