from django.db import connection
from django.test import TestCase

from tracks.models import Genre


class DatabaseHardeningTests(TestCase):
    def test_genre_catalog_has_at_least_twenty_rows(self):
        self.assertGreaterEqual(Genre.objects.count(), 20)

    def test_eight_updated_at_triggers_exist(self):
        expected_triggers = {
            "trg_user_set_updated_at",
            "trg_artist_set_updated_at",
            "trg_genre_set_updated_at",
            "trg_track_set_updated_at",
            "trg_playlist_set_updated_at",
            "trg_playlist_track_set_updated_at",
            "trg_order_set_updated_at",
            "trg_order_item_set_updated_at",
        }
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT tgname
                FROM pg_trigger
                WHERE NOT tgisinternal
                  AND tgname LIKE 'trg_%_set_updated_at'
                """
            )
            found = {row[0] for row in cursor.fetchall()}
        self.assertTrue(expected_triggers.issubset(found))

    def test_raw_sql_insert_into_genre_populates_timestamps_and_id(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO genre (name) VALUES (%s) RETURNING id, created_at, updated_at",
                ["raw_sql_test_genre"],
            )
            row = cursor.fetchone()
        self.assertIsNotNone(row[0])
        self.assertIsNotNone(row[1])
        self.assertIsNotNone(row[2])
