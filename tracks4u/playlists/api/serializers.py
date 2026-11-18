from rest_framework import serializers

from playlists.models import Playlist, PlaylistTrack
from tracks.api.serializers import TrackSerializer


class PlaylistTrackSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    track_id = serializers.IntegerField(source="track.id", read_only=True)

    class Meta:
        model = PlaylistTrack
        fields = [
            "id",
            "playlist_id",
            "track_id",
            "track",
            "position",
            "added_at",
            "updated_at",
        ]


class PlaylistSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    items = PlaylistTrackSerializer(source="playlist_tracks", many=True, read_only=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=60),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Playlist
        fields = [
            "id",
            "owner_id",
            "owner_username",
            "name",
            "description",
            "tags",
            "cover_image",
            "is_public",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = ["id", "owner_id", "owner_username", "created_at", "updated_at", "items"]

    def validate_name(self, value: str) -> str:
        if not value or not value.strip():
            raise serializers.ValidationError("Playlist name cannot be empty.")
        return value.strip()


class PlaylistAddTrackSerializer(serializers.Serializer):
    track_id = serializers.IntegerField(min_value=1)


class PlaylistReorderSerializer(serializers.Serializer):
    track_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )
