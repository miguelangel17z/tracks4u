import django.contrib.postgres.fields
from django.db import migrations, models

import core.uploads


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="Artist",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("stage_name", models.CharField(max_length=150, unique=True)),
                ("bio", models.TextField(blank=True, null=True)),
                ("country", models.CharField(blank=True, max_length=100, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "artist",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="ArtistGenre",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                "db_table": "artist_genre",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Genre",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=80, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "genre",
                "ordering": ["name"],
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="Track",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("subgenre", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "language",
                    models.CharField(blank=True, default="es", max_length=60, null=True),
                ),
                (
                    "mood_tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=60),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                ("bpm", models.SmallIntegerField(blank=True, null=True)),
                (
                    "track_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("ORIGINAL", "Original"),
                            ("REMIX", "Remix"),
                            ("COVER", "Cover"),
                        ],
                        default="ORIGINAL",
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "price",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "audio_file",
                    models.FileField(
                        blank=True,
                        max_length=255,
                        null=True,
                        upload_to=core.uploads.track_audio_path,
                    ),
                ),
                (
                    "cover_image",
                    models.ImageField(
                        blank=True,
                        max_length=255,
                        null=True,
                        upload_to=core.uploads.track_cover_path,
                    ),
                ),
                ("duration_sec", models.IntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "track",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="TrackGenre",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                "db_table": "track_genre",
                "managed": False,
            },
        ),
    ]
