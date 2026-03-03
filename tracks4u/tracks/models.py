from django.db import models

class Track(models.Model): 
    title = models.CharField(max_length=200)
    audio_file = models.FileField(upload_to='tracks_files/') 
    price = models.DecimalField(max_digits=8, decimal_places=2) #precio maximo: 999.999.99
    bpm = models.IntegerField()
    is_sold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    cover_image = models.ImageField(upload_to='tracks_covers/', null=True, blank=True)
    genre = models.CharField(max_length=100, blank=True, null=True)
    stock = models.PositiveIntegerField(null=True, blank=True)




