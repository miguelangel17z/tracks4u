from pathlib import Path

from django.conf import settings
from django.db import migrations


def apply_schema(apps, schema_editor):
    """Aplica database/schema.sql de forma idempotente en PostgreSQL."""
    if schema_editor.connection.vendor != "postgresql":
        return

    schema_path = Path(settings.SCHEMA_SQL_PATH)
    if not schema_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de esquema SQL en la ruta: {schema_path}"
        )

    raw_sql = schema_path.read_text(encoding="utf-8")
    filtered_lines = [
        line
        for line in raw_sql.splitlines()
        if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    ]
    sql = "\n".join(filtered_lines)

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(sql)


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(apply_schema, reverse_code=migrations.RunPython.noop),
    ]
