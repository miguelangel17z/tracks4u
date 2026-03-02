from rest_framework import serializers
from users.models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'created_at']

    # Configuraciones extras
        extra_kwargs ={
            "password":{'write_only':True, 'min_length':8},
            "created_at":{'read_only'}
        }


        
       

