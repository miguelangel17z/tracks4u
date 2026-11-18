from decimal import Decimal

import boto3
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from moto import mock_aws
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tracks.models import Artist, Genre, Track
from users.models import User

TEST_BUCKET = "tracks4u-test-tracks-bucket"


@override_settings(
    AWS_STORAGE_BUCKET_NAME=TEST_BUCKET,
    AWS_S3_REGION_NAME="us-east-1",
    AWS_ACCESS_KEY_ID="testing",
    AWS_SECRET_ACCESS_KEY="testing",
    AWS_QUERYSTRING_AUTH=True,
    CELERY_TASK_ALWAYS_EAGER=True,
    NOTIFICATION_MODE="MOCK",
)
class TracksAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.regular_user = User.objects.create_user(
            username="regular_u",
            email="regular_u@example.com",
            password="SafePassword123!",
        )
        self.artist_user = User.objects.create_user(
            username="artist_u",
            email="artist_u@example.com",
            password="SafePassword123!",
        )
        self.artist = Artist.objects.create(
            user=self.artist_user,
            stage_name="DJ Test",
            country="Colombia",
        )
        self.genre_pop, _ = Genre.objects.get_or_create(name="Pop")
        self.genre_lofi, _ = Genre.objects.get_or_create(name="Lo-fi")

        self.regular_token = str(RefreshToken.for_user(self.regular_user).access_token)
        self.artist_token = str(RefreshToken.for_user(self.artist_user).access_token)

    def test_upload_track_requires_artist_and_at_least_one_genre(self):
        with mock_aws():
            s3 = boto3.client(
                "s3",
                region_name="us-east-1",
                aws_access_key_id="testing",
                aws_secret_access_key="testing",
            )
            s3.create_bucket(Bucket=TEST_BUCKET)

            # Non-artist gets 403
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.regular_token}")
            audio1 = SimpleUploadedFile("demo.mp3", b"ID3content", content_type="audio/mpeg")
            res_forbidden = self.client.post(
                "/api/tracks/",
                {
                    "title": "Non Artist Song",
                    "price": "3.99",
                    "genre_ids": [self.genre_pop.id],
                    "audio_file": audio1,
                },
                format="multipart",
            )
            self.assertEqual(res_forbidden.status_code, 403)

            # Artist without genres gets 400
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.artist_token}")
            audio2 = SimpleUploadedFile("demo2.mp3", b"ID3content", content_type="audio/mpeg")
            res_no_genre = self.client.post(
                "/api/tracks/",
                {
                    "title": "Genreless Song",
                    "price": "3.99",
                    "audio_file": audio2,
                },
                format="multipart",
            )
            self.assertEqual(res_no_genre.status_code, 400)

            # Valid artist upload succeeds (201) with subgenre, mood_tags, and presigned S3 URL
            audio3 = SimpleUploadedFile("demo3.mp3", b"ID3content", content_type="audio/mpeg")
            res_ok = self.client.post(
                "/api/tracks/",
                {
                    "title": "Midnight Study",
                    "subgenre": "Chillhop",
                    "mood_tags": "chill, study",
                    "bpm": 85,
                    "track_type": "ORIGINAL",
                    "language": "instrumental",
                    "price": "4.50",
                    "genre_ids": [self.genre_lofi.id],
                    "audio_file": audio3,
                },
                format="multipart",
            )
            self.assertEqual(res_ok.status_code, 201)
            self.assertEqual(res_ok.data["subgenre"], "Chillhop")
            self.assertEqual(res_ok.data["mood_tags"], ["chill", " study".strip()])
            self.assertIn("price", res_ok.data)
            self.assertTrue("X-Amz-Signature" in res_ok.data["audio_file"] or "Signature=" in res_ok.data["audio_file"])

            # Search and filter
            self.client.credentials()
            res_search = self.client.get("/api/tracks/?q=Midnight")
            self.assertEqual(res_search.status_code, 200)
            self.assertEqual(len(res_search.data["results"]), 1)

            res_genre = self.client.get(f"/api/tracks/?genre={self.genre_lofi.id}")
            self.assertEqual(len(res_genre.data["results"]), 1)
