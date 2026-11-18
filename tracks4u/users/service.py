from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class AuthService:
    @staticmethod
    def login(password: str, email: str = None, username: str = None) -> dict:
        user = None

        if email:
            try:
                lookup = User.objects.get(email=email)
                user = authenticate(username=lookup.username, password=password)
            except User.DoesNotExist:
                user = None
        elif username:
            user = authenticate(username=username, password=password)

        if user is None:
            raise ValueError("Incorrect username or password")

        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class RegisterService:
    @staticmethod
    def register(data: dict) -> User:
        extra = {}
        for field in ("country", "birth_date", "gender", "ethnicity"):
            if field in data and data[field] is not None:
                extra[field] = data[field] or None
        return User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            **extra,
        )


class UpdateProfileService:
    @staticmethod
    def updateProfile(user: User, data: dict) -> User:
        if "username" in data and data["username"]:
            user.username = data["username"]
        if "email" in data and data["email"]:
            user.email = data["email"]
        if "password" in data and data["password"]:
            user.set_password(data["password"])

        for field in ("country", "birth_date", "gender", "ethnicity"):
            if field in data:
                val = data[field]
                setattr(user, field, val if val != "" else None)

        user.save()
        return user
