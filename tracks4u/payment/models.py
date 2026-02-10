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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.PROTECT)



    

