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
    mood_tags = serializers.ListField(
        child=serializers.CharField(max_length=60),
        required=False,
        allow_null=True,
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
        read_only_fields = [
            "id",
            "artist",
            "genres",
            "duration_sec",
            "created_at",
            "updated_at",
        ]

    def validate_bpm(self, value):
        if value is not None and not (1 <= value <= 300):
            raise serializers.ValidationError("BPM must be between 1 and 300.")
        return value

    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Price must be >= 0.")
        return value


class ArtistSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)

    class Meta:
        model = Artist
        fields = [
            "id",
            "user_id",
            "stage_name",
            "bio",
            "country",
            "genres",
            "tracks",
            "created_at",
            "updated_at",
        ]
