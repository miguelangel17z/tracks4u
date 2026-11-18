from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("username", models.CharField(max_length=50, unique=True)),
                ("email", models.EmailField(max_length=255, unique=True)),
                ("password", models.TextField()),
                ("country", models.CharField(blank=True, max_length=100, null=True)),
                ("birth_date", models.DateField(blank=True, null=True)),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("FEMALE", "Female"),
                            ("MALE", "Male"),
                            ("NON_BINARY", "Non-binary"),
                            ("PREFER_NOT_TO_SAY", "Prefer not to say"),
                        ],
                        max_length=50,
                        null=True,
                    ),
                ),
                ("ethnicity", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "app_role",
                    models.CharField(
                        choices=[("user", "User"), ("sysadmin", "Sysadmin")],
                        default="user",
                        max_length=20,
                    ),
                ),
                ("last_login", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "user",
                "managed": False,
            },
        ),
    ]
