from rest_framework import serializers


class EventAckSerializer(serializers.Serializer):
    last_id = serializers.IntegerField(min_value=0)
