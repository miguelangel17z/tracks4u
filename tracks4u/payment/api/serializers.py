from rest_framework import serializers

from payment.models import Order, OrderItem


class OrderCreateSerializer(serializers.Serializer):
    track_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        max_length=50,
    )
    payment_method = serializers.ChoiceField(
        choices=[c[0] for c in Order.PAYMENT_METHOD_CHOICES],
        default="CARD",
    )


class OrderItemSerializer(serializers.ModelSerializer):
    track_id = serializers.IntegerField(source="track.id", read_only=True)
    track_title = serializers.CharField(source="track.title", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "track_id",
            "track_title",
            "price_paid",
            "currency",
            "created_at",
        ]


class OrderSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user_id",
            "total_amount",
            "currency",
            "payment_method",
            "status",
            "created_at",
            "updated_at",
            "items",
        ]


class PurchaseSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    purchased_at = serializers.DateTimeField(source="created_at", read_only=True)
    track = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order_id",
            "track",
            "price_paid",
            "currency",
            "purchased_at",
        ]

    def get_track(self, obj: OrderItem) -> dict:
        track = obj.track
        artist_name = track.artist.stage_name if getattr(track, "artist", None) else None
        cover_url = None
        if track.cover_image:
            try:
                cover_url = track.cover_image.url
            except Exception:
                cover_url = str(track.cover_image)
        audio_url = None
        if track.audio_file:
            try:
                audio_url = track.audio_file.url
            except Exception:
                audio_url = str(track.audio_file)
        return {
            "id": track.id,
            "title": track.title,
            "artist": artist_name,
            "bpm": track.bpm,
            "cover_url": cover_url,
            "audio_url": audio_url,
        }
