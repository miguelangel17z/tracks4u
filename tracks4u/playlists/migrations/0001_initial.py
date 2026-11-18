import django.contrib.postgres.fields
from django.db import migrations, models

import core.uploads
import core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="Playlist",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=150)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=60),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "cover_image",
                    models.ImageField(
                        blank=True,
                        max_length=255,
                        null=True,
                        upload_to=core.uploads.playlist_cover_path,
                        validators=[core.validators.validate_image_file],
                    ),
                ),
                ("is_public", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "playlist",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="PlaylistTrack",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("position", models.IntegerField()),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "playlist_track",
                "ordering": ["position"],
                "managed": False,
            },
        ),
    ]
