from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.uploads import track_audio_path, track_cover_path


class Genre(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=80, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "genre"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Artist(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="user_id",
        related_name="artist",
    )
    stage_name = models.CharField(max_length=150, unique=True)
    bio = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    genres = models.ManyToManyField(
        Genre,
        through="ArtistGenre",
        related_name="artists",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "artist"

    def __str__(self):
        return self.stage_name


class ArtistGenre(models.Model):
    id = models.BigAutoField(primary_key=True)
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        db_column="artist_id",
        related_name="artist_genres",
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.PROTECT,
        db_column="genre_id",
        related_name="genre_artists",
    )

    class Meta:
        managed = False
        db_table = "artist_genre"
        unique_together = [("artist", "genre")]


class Track(models.Model):
    TRACK_TYPE_CHOICES = [
        ("ORIGINAL", "Original"),
        ("REMIX", "Remix"),
        ("COVER", "Cover"),
    ]

    id = models.BigAutoField(primary_key=True)
    artist = models.ForeignKey(
        Artist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="artist_id",
        related_name="tracks",
    )
    title = models.CharField(max_length=255)
    subgenre = models.CharField(max_length=100, null=True, blank=True)
    language = models.CharField(max_length=60, null=True, blank=True, default="es")
    mood_tags = ArrayField(models.CharField(max_length=60), null=True, blank=True)
    bpm = models.SmallIntegerField(null=True, blank=True)
    track_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default="ORIGINAL",
        choices=TRACK_TYPE_CHOICES,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    audio_file = models.FileField(
        upload_to=track_audio_path,
        max_length=255,
        null=True,
        blank=True,
    )
    cover_image = models.ImageField(
        upload_to=track_cover_path,
        max_length=255,
        null=True,
        blank=True,
    )
    duration_sec = models.IntegerField(null=True, blank=True)
    genres = models.ManyToManyField(
        Genre,
        through="TrackGenre",
        related_name="tracks",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "track"

    def __str__(self):
        return self.title


class TrackGenre(models.Model):
    id = models.BigAutoField(primary_key=True)
    track = models.ForeignKey(
        Track,
        on_delete=models.CASCADE,
        db_column="track_id",
        related_name="track_genres",
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.PROTECT,
        db_column="genre_id",
        related_name="genre_tracks",
    )

    class Meta:
        managed = False
        db_table = "track_genre"
        unique_together = [("track", "genre")]
