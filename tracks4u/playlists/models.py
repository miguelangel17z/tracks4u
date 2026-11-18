from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.uploads import playlist_cover_path


class Playlist(models.Model):
    id = models.BigAutoField(primary_key=True)
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        db_column="owner_id",
        related_name="playlists",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    tags = ArrayField(models.CharField(max_length=60), null=True, blank=True)
    cover_image = models.ImageField(
        upload_to=playlist_cover_path,
        max_length=255,
        null=True,
        blank=True,
    )
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "playlist"

    def __str__(self):
        return f"{self.name} ({self.owner})"


class PlaylistTrack(models.Model):
    id = models.BigAutoField(primary_key=True)
    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.CASCADE,
        db_column="playlist_id",
        related_name="playlist_tracks",
    )
    track = models.ForeignKey(
        "tracks.Track",
        on_delete=models.CASCADE,
        db_column="track_id",
        related_name="playlist_entries",
    )
    position = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "playlist_track"
        ordering = ["position"]
        unique_together = [("playlist", "track")]

    def __str__(self):
        return f"{self.playlist_id} #{self.position} -> {self.track_id}"
