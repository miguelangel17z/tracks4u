import uuid

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="TelemetryEvent",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("event_id", models.UUIDField(default=uuid.uuid4, unique=True)),
                ("event_type", models.CharField(max_length=40)),
                ("ts", models.DateTimeField(default=django.utils.timezone.now)),
                ("session_id", models.CharField(max_length=64)),
                (
                    "device",
                    models.CharField(
                        choices=[
                            ("web_desktop", "Web Desktop"),
                            ("web_mobile", "Web Mobile"),
                            ("web_tablet", "Web Tablet"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=20,
                    ),
                ),
                ("geo", models.JSONField(blank=True, null=True)),
                (
                    "entrypoint",
                    models.CharField(
                        choices=[
                            ("home", "Home"),
                            ("search", "Search"),
                            ("artist_profile", "Artist Profile"),
                            ("playlist", "Playlist"),
                            ("track_page", "Track Page"),
                            ("library", "Library"),
                            ("external_link", "External Link"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=20,
                    ),
                ),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("acked_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "telemetry_event",
                "managed": False,
            },
        ),
    ]
