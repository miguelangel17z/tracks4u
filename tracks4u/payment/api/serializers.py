from rest_framework import serializers
from payment.models import License
from tracks.models import Track
from users.models import User




class LicenseSerializer(serializers.ModelSerializer):
    track = serializers.PrimaryKeyRelatedField(
        queryset=Track.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    class Meta:
        model = License
        fields = ['user','track','license_type']

        
        



        
       

