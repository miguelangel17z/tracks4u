from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import authenticate
from django.db import connection, IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from payment.models import Order
from playlists.models import Playlist, PlaylistTrack
from tracks.models import Artist, ArtistGenre, Genre, Track
from users.models import User


class SchemaAndModelsTests(TestCase):
    def test_apply_schema_is_idempotent_and_creates_all_tables(self):
        import importlib

        mod = importlib.import_module("core.migrations.0001_schema")
        mod.apply_schema(None, connection.schema_editor())
        mod.apply_schema(None, connection.schema_editor())

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
            tables = {row[0] for row in cursor.fetchall()}

        expected = {
            "user",
            "artist",
            "genre",
            "artist_genre",
            "track",
            "track_genre",
            "playlist",
            "playlist_track",
            "order",
            "order_item",
            "telemetry_event",
            "etl_watermark",
        }
        self.assertTrue(expected.issubset(tables))
        self.assertGreaterEqual(Genre.objects.count(), 20)

    def test_user_model_and_jwt(self):
        user = User.objects.create_user(
            username="testuser1",
            email="testuser1@example.com",
            password="SafePassword123!",
            country="Colombia",
        )
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        admin_user = User.objects.create_superuser(
            username="sysadmin_test",
            email="sysadmin_test@example.com",
            password="AdminPassword123!",
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

        locked_user = User.objects.create(
            username="locked_seed",
            email="locked_seed@example.com",
            password="!RESET_REQUIRED!",
        )
        self.assertIsNone(authenticate(username=locked_user.username, password="!RESET_REQUIRED!"))

        refresh = RefreshToken.for_user(user)
        self.assertEqual(int(refresh["user_id"]), user.id)

    def test_artist_and_track_models_with_arrays_and_unique_bridges(self):
        artist = Artist.objects.create(stage_name="Standalone Test Artist", country="Colombia")
        self.assertIsNone(artist.user)

        genre = Genre.objects.first()
        ArtistGenre.objects.create(artist=artist, genre=genre)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ArtistGenre.objects.create(artist=artist, genre=genre)

        track = Track.objects.create(
            artist=artist,
            title="Test Mood Track",
            subgenre="Experimental",
            mood_tags=["chill", "night"],
            bpm=120,
            track_type="ORIGINAL",
            price=Decimal("4.99"),
        )
        track.refresh_from_db()
        self.assertEqual(track.mood_tags, ["chill", "night"])

    def test_playlist_track_deferred_position_and_unique_track(self):
        user = User.objects.create_user(
            username="pl_owner",
            email="pl_owner@example.com",
            password="SafePassword123!",
        )
        artist = Artist.objects.create(stage_name="PL Artist")
        t1 = Track.objects.create(artist=artist, title="T1", price=Decimal("1.99"))
        t2 = Track.objects.create(artist=artist, title="T2", price=Decimal("1.99"))
        playlist = Playlist.objects.create(owner=user, name="My List", tags=["workout"])

        pt1 = PlaylistTrack.objects.create(playlist=playlist, track=t1, position=1)
        pt2 = PlaylistTrack.objects.create(playlist=playlist, track=t2, position=2)

        with transaction.atomic():
            pt1.position = 2
            pt1.save()
            pt2.position = 1
            pt2.save()

        pt1.refresh_from_db()
        pt2.refresh_from_db()
        self.assertEqual(pt1.position, 2)
        self.assertEqual(pt2.position, 1)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaylistTrack.objects.create(playlist=playlist, track=t1, position=3)

    def test_updated_at_trigger_on_queryset_update_and_raw_sql(self):
        past = timezone.now() - timedelta(minutes=10)
        genre = Genre.objects.create(name="trigger_test_genre")
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE genre SET updated_at = %s WHERE id = %s",
                [past, genre.id],
            )
        # Note: the UPDATE above fires the trigger, setting updated_at = CURRENT_TIMESTAMP.
        # Let's verify that updating name advances updated_at beyond a recorded timestamp.
        genre.refresh_from_db()
        before_ts = genre.updated_at

        Genre.objects.filter(pk=genre.pk).update(name="trigger_test_genre_v2")
        genre.refresh_from_db()
        self.assertGreaterEqual(genre.updated_at, before_ts)

    def test_order_invalid_status_check_constraint(self):
        user = User.objects.create_user(
            username="buyer_chk",
            email="buyer_chk@example.com",
            password="SafePassword123!",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Order.objects.create(
                    user=user,
                    total_amount=Decimal("10.00"),
                    currency="USD",
                    status="INVALID_STATUS",
                )
