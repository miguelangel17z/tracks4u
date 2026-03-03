from rest_framework import serializers
from tracks.models import Track


class TrackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Track
        fields = [
            "id",
            "title",
            "audio_file",
            "price",
            "bpm",
            "created_at",
            "cover_image",
            "genre",
            "stock",
        ]
        read_only_fields = ["id", "created_at"]