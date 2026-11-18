from datetime import date
from rest_framework import serializers

from users.models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        if not attrs.get("username") and not attrs.get("email"):
            raise serializers.ValidationError("Username or email is required.")
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "country",
            "birth_date",
            "gender",
            "ethnicity",
            "created_at",
        ]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
            "created_at": {"read_only": True},
        }


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "country",
            "birth_date",
            "gender",
            "ethnicity",
        ]
        extra_kwargs = {
            "username": {"required": False},
            "email": {"required": False},
            "password": {"required": False, "write_only": True, "min_length": 8},
            "country": {"required": False, "allow_null": True, "allow_blank": True},
            "birth_date": {"required": False, "allow_null": True},
            "gender": {"required": False, "allow_null": True, "allow_blank": True},
            "ethnicity": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def validate_birth_date(self, value):
        if value is None:
            return value
        today = date.today()
        if value > today:
            raise serializers.ValidationError("Birth date cannot be in the future.")
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise serializers.ValidationError("Minimum age is 13 years.")
        return value

    def validate_gender(self, value):
        if not value:
            return None
        valid = {choice[0] for choice in User.GENDER_CHOICES}
        if value not in valid:
            raise serializers.ValidationError(f"Invalid gender. Must be one of {sorted(valid)}.")
        return value
