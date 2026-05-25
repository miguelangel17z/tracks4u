from rest_framework import serializers


class SalesByPeriodSerializer(serializers.Serializer):
    period  = serializers.CharField()
    labels  = serializers.ListField(child=serializers.CharField())
    values  = serializers.ListField(child=serializers.IntegerField())
    total_sales = serializers.IntegerField()


class RevenueBreakdownItemSerializer(serializers.Serializer):
    count         = serializers.IntegerField()
    unit_price_usd = serializers.FloatField()
    revenue_usd   = serializers.FloatField()


class RevenueSerializer(serializers.Serializer):
    period            = serializers.CharField()
    total_revenue_usd = serializers.FloatField()
    breakdown         = serializers.DictField(child=RevenueBreakdownItemSerializer())
    labels            = serializers.ListField(child=serializers.CharField())
    values            = serializers.ListField(child=serializers.FloatField())


class TrackItemSerializer(serializers.Serializer):
    id          = serializers.IntegerField()
    title       = serializers.CharField()
    genre       = serializers.CharField()
    sales_count = serializers.IntegerField()
    is_sold     = serializers.BooleanField()


class TopTracksSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    values = serializers.ListField(child=serializers.IntegerField())
    tracks = TrackItemSerializer(many=True)


class TopGenresSerializer(serializers.Serializer):
    period = serializers.CharField()
    labels = serializers.ListField(child=serializers.CharField())
    values = serializers.ListField(child=serializers.IntegerField())


class SummarySerializer(serializers.Serializer):
    period            = serializers.CharField()
    total_sales       = serializers.IntegerField()
    total_revenue_usd = serializers.FloatField()
    total_tracks      = serializers.IntegerField()
    top_track         = serializers.CharField()
