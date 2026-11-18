from rest_framework import serializers


class SalesByPeriodSerializer(serializers.Serializer):
    period = serializers.CharField()
    labels = serializers.ListField(child=serializers.CharField())
    values = serializers.ListField(child=serializers.IntegerField())
    total_sales = serializers.IntegerField()


class RevenueBreakdownItemSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    unit_price_usd = serializers.FloatField()
    revenue_usd = serializers.FloatField()


class RevenueSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_revenue_usd = serializers.FloatField()
    breakdown = serializers.DictField(child=RevenueBreakdownItemSerializer())
    labels = serializers.ListField(child=serializers.CharField())
    values = serializers.ListField(child=serializers.FloatField())


class TrackItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    genres = serializers.CharField()
    items_sold = serializers.IntegerField()
    price = serializers.FloatField(required=False, default=0.0)


class TopTracksSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    values = serializers.ListField(child=serializers.IntegerField())
    tracks = TrackItemSerializer(many=True)


class TopGenresSerializer(serializers.Serializer):
    period = serializers.CharField()
    labels = serializers.ListField(child=serializers.CharField())
    values = serializers.ListField(child=serializers.IntegerField())


class SummarySerializer(serializers.Serializer):
    period = serializers.CharField()
    total_sales = serializers.IntegerField()
    total_revenue_usd = serializers.FloatField()
    avg_ticket_usd = serializers.FloatField(required=False, default=0.0)
    total_tracks = serializers.IntegerField()
    top_track = serializers.CharField()
