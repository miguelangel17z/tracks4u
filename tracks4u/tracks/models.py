from django.db import models

class Track(models.Model): 
    title = models.CharField(max_length=200)
    audio_file = models.FileField(upload_to='tracks_files/') 
    bpm = models.PositiveIntegerField()
    is_sold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    cover_image = models.ImageField(upload_to='tracks_covers/', null=True, blank=True)
    genre = models.CharField(max_length=100, blank=True, null=True)
    sales_count = models.PositiveIntegerField(default=0)




