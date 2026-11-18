from rest_framework import serializers

from tracks.models import Artist, Genre, Track


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class ArtistSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ["id", "stage_name", "country"]


class TrackSerializer(serializers.ModelSerializer):
    artist = ArtistSummarySerializer(read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    genre_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Track
        fields = [
            "id",
            "title",
            "artist",
            "genres",
            "genre_ids",
            "subgenre",
            "language",
            "mood_tags",
            "bpm",
            "track_type",
            "price",
            "audio_file",
            "cover_image",
            "duration_sec",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "artist", "genres", "duration_sec", "created_at", "updated_at"]
