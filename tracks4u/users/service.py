from typing import List, Optional

from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from tracks.models import Artist, ArtistGenre, Genre
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


class ArtistService:
    """Servicio para onboarding y edición del perfil de artista de un usuario."""

    @staticmethod
    def become_artist(
        user: User,
        stage_name: str,
        bio: str = "",
        country: Optional[str] = None,
        genre_ids: Optional[List[int]] = None,
    ) -> Artist:
        if Artist.objects.filter(user=user).exists():
            raise ValueError("User is already an artist.")
        if not stage_name or not stage_name.strip():
            raise ValueError("stage_name is required.")
        clean_name = stage_name.strip()
        if Artist.objects.filter(stage_name=clean_name).exists():
            raise ValueError("stage_name is already taken.")

        with transaction.atomic():
            artist = Artist.objects.create(
                user=user,
                stage_name=clean_name,
                bio=bio or "",
                country=country or user.country,
            )
            if genre_ids:
                genres = list(Genre.objects.filter(id__in=genre_ids))
                for g in genres:
                    ArtistGenre.objects.get_or_create(artist=artist, genre=g)
            return artist

    @staticmethod
    def update_artist(user: User, data: dict) -> Artist:
        artist = Artist.objects.filter(user=user).first()
        if artist is None:
            raise PermissionError("User is not an artist.")

        with transaction.atomic():
            if "stage_name" in data and data["stage_name"]:
                clean_name = data["stage_name"].strip()
                if (
                    Artist.objects.filter(stage_name=clean_name)
                    .exclude(id=artist.id)
                    .exists()
                ):
                    raise ValueError("stage_name is already taken.")
                artist.stage_name = clean_name
            if "bio" in data:
                artist.bio = data["bio"] or ""
            if "country" in data:
                artist.country = data["country"] or None
            artist.save()

            if "genre_ids" in data and data["genre_ids"] is not None:
                genres = list(Genre.objects.filter(id__in=data["genre_ids"]))
                ArtistGenre.objects.filter(artist=artist).delete()
                for g in genres:
                    ArtistGenre.objects.get_or_create(artist=artist, genre=g)

            return artist
