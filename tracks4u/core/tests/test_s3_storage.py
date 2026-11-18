from decimal import Decimal
import io

import boto3
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from moto import mock_aws
from PIL import Image

from core.validators import validate_audio_file, validate_image_file
from tracks.models import Artist, Track

TEST_BUCKET = "tracks4u-test-bucket"


class UploadValidatorsTests(SimpleTestCase):
    def test_audio_validator_accepts_valid_extensions_and_rejects_exe_or_oversized(self):
        valid_mp3 = SimpleUploadedFile("song.mp3", b"ID3dummydata", content_type="audio/mpeg")
        validate_audio_file(valid_mp3)

        valid_opus = SimpleUploadedFile("song.opus", b"OggSdummydata", content_type="audio/ogg")
        validate_audio_file(valid_opus)

        bad_exe = SimpleUploadedFile("malware.exe", b"MZ...", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_audio_file(bad_exe)

        oversized = SimpleUploadedFile("huge.mp3", b"a", content_type="audio/mpeg")
        oversized.size = 60 * 1024 * 1024
        with self.assertRaises(ValidationError):
            validate_audio_file(oversized)

    def test_image_validator_accepts_valid_image_and_rejects_corrupt_or_oversized(self):
        buf = io.BytesIO()
        Image.new("RGB", (16, 16), color="red").save(buf, format="PNG")
        valid_img = SimpleUploadedFile("cover.png", buf.getvalue(), content_type="image/png")
        validate_image_file(valid_img)

        not_img = SimpleUploadedFile("fake.png", b"not an image", content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_image_file(not_img)

        oversized_img = SimpleUploadedFile("big.png", buf.getvalue(), content_type="image/png")
        oversized_img.size = 6 * 1024 * 1024
        with self.assertRaises(ValidationError):
            validate_image_file(oversized_img)


@override_settings(
    AWS_STORAGE_BUCKET_NAME=TEST_BUCKET,
    AWS_S3_REGION_NAME="us-east-1",
    AWS_ACCESS_KEY_ID="testing",
    AWS_SECRET_ACCESS_KEY="testing",
    AWS_QUERYSTRING_AUTH=True,
)
class S3StorageIntegrationTests(TestCase):
    def test_track_upload_stores_in_s3_with_expected_key_and_presigned_url(self):
        with mock_aws():
            s3 = boto3.client(
                "s3",
                region_name="us-east-1",
                aws_access_key_id="testing",
                aws_secret_access_key="testing",
            )
            s3.create_bucket(Bucket=TEST_BUCKET)

            artist = Artist.objects.create(stage_name="S3 Test Artist")
            audio_file = SimpleUploadedFile(
                "original_name.mp3",
                b"ID3mockmp3content",
                content_type="audio/mpeg",
            )
            track = Track.objects.create(
                artist=artist,
                title="S3 Hosted Track",
                price=Decimal("2.99"),
                audio_file=audio_file,
            )

            self.assertTrue(track.audio_file.name.startswith(f"audio/{artist.id}/"))
            self.assertTrue(track.audio_file.name.endswith(".mp3"))
            self.assertNotIn("original_name", track.audio_file.name)

            head = s3.head_object(Bucket=TEST_BUCKET, Key=track.audio_file.name)
            self.assertEqual(head["ContentLength"], len(b"ID3mockmp3content"))

            presigned_url = track.audio_file.url
            self.assertTrue(
                "X-Amz-Signature" in presigned_url or "Signature=" in presigned_url,
                f"Expected presigned URL, got: {presigned_url}",
            )
