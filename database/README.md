# Base de datos RDS PostgreSQL — Tracks4U

Este directorio contiene la fuente de verdad del esquema relacional de **Tracks4U**, los datos semilla, los scripts de endurecimiento de permisos para Amazon RDS PostgreSQL y las herramientas de verificación del contrato de datos.

## Estructura de archivos

| Archivo | Propósito |
|---|---|
| `schema.sql` | DDL idempotente (PostgreSQL 14+): 12 tablas, restricciones `CHECK`/`UNIQUE`, índices, función y 8 triggers `trg_<tabla>_set_updated_at`, y catálogo base de 20 géneros. |
| `seed.sql` | Datos iniciales idempotentes: 6 usuarios (con contraseña bloqueada `!RESET_REQUIRED!`), 14 artistas con sus géneros, 36 canciones base, 3 playlists y 8 filas iniciales en `etl_watermark`. |
| `seed_media_updates.sql` | Actualización idempotente de las 36 canciones del seed con títulos completos corregidos, `artist_id`, `duration_sec` reales (extraídos con `mutagen`), precios, idioma, keys S3 (`audio_file`, `cover_image`) y relaciones en `track_genre`. Generado por `python manage.py sync_seed_media --export-sql`. |
| `rds/grants.sql` | Script `psql` idempotente que configura los privilegios de `app_user` y la superficie restringida de `ingest_user` (Glue de Juanc) según `AGENTS/design.md` §6. |
| `rds/verify.sql` | Script `psql` que verifica las 12 tablas, los 8 triggers `updated_at`, los ≥ 20 géneros y (si se pasa `-v ingest_user=...`) los privilegios positivos y negativos del rol de ingesta. |
| `check_contract_er.py` | Verifica con `pglast` que el diagrama Mermaid ER de `AGENTS/contrato.md` coincida exactamente con `database/schema.sql`. |

---

## Orden de despliegue en la EC2 (`design.md` §3.5)

La instancia RDS (`tracks4u-postgres-dev.c4qkjciamuny.us-east-1.rds.amazonaws.com`) vive en una subred privada, por lo que todos los comandos contra RDS se ejecutan desde la **EC2 del proyecto** con `PGSSLMODE=require`.

Variables de entorno útiles para la sesión en la EC2:

```bash
export PGHOST=tracks4u-postgres-dev.c4qkjciamuny.us-east-1.rds.amazonaws.com
export PGPORT=5432
export PGDATABASE=tracks4u
export PGUSER=tracks4u_app
export PGSSLMODE=require
```

### 1. Aplicar esquema y migraciones de Django (`migrate`)

Puedes inicializar el esquema con `psql` o directamente con `manage.py migrate` (la migración `core.0001_schema` ejecuta `database/schema.sql` de forma idempotente y luego Django crea sus tablas internas `django_*` y `auth_*`):

```bash
# Opción A: aplicar schema.sql explícitamente y luego migrate
psql -f database/schema.sql
cd tracks4u && python manage.py migrate

# Opción B: directamente con migrate (aplica schema.sql vía core.0001_schema)
cd tracks4u && python manage.py migrate
```

### 2. Aplicar permisos (`database/rds/grants.sql`)

Debe ejecutarse con el rol dueño de las tablas después de `migrate` (y re-ejecutarse tras cualquier cambio de esquema). Requiere pasar las variables `-v db_name`, `-v owner_user`, `-v app_user` y `-v ingest_user`:

```bash
psql \
  -v db_name=tracks4u \
  -v owner_user=tracks4u_app \
  -v app_user=tracks4u_app \
  -v ingest_user=<nombre_rol_ingesta_glue> \
  -f database/rds/grants.sql
```

> **Nota:** Si el rol de ingesta aún no ha sido creado por el administrador de RDS, créalo primero o ejecuta `verify.sql` sin `-v ingest_user` para validar tablas, triggers y catálogo.

### 3. Cargar datos iniciales (`database/seed.sql`)

```bash
psql -f database/seed.sql
```

### 4. Sincronizar canciones y portadas reales con S3 y RDS (`sync_seed_media`)

Los 36 archivos `.opus` y las 33 portadas en `cancionesCovers/tracks4u/` se sincronizan hacia el bucket S3 (`tracks4u-datalake-463790652932-us-east-1`) y actualizan las filas `1..36` de `track` y `track_genre` en RDS:

```bash
cd tracks4u

# 1) Previsualizar mapeo y verificar archivos locales sin tocar S3 ni RDS
python manage.py sync_seed_media --dry-run

# 2) Subir archivos de audio y portadas a S3 y actualizar metadatos en RDS
python manage.py sync_seed_media

# Opciones adicionales:
#   Solo subir archivos a S3 sin conectar a RDS:
python manage.py sync_seed_media --skip-db
#   Solo actualizar metadatos en RDS (si los objetos ya están en S3):
python manage.py sync_seed_media --skip-s3
#   Exportar SQL idempotente para aplicar por psql directo:
python manage.py sync_seed_media --export-sql ../database/seed_media_updates.sql
```

Si prefieres aplicar las actualizaciones de metadatos por `psql`:

```bash
psql -f database/seed_media_updates.sql
```

### 5. Ejecutar verificación (`database/rds/verify.sql`)

```bash
# Verificación de tablas, triggers y catálogo de géneros:
psql -f database/rds/verify.sql

# Verificación completa incluyendo permisos del rol de ingesta:
psql -v ingest_user=<nombre_rol_ingesta_glue> -f database/rds/verify.sql
```

---

## Prueba de carga incremental con Juanc (`genre` / `zz_incremental_test`)

Según `AGENTS/tasks.md` (§6.b) y `AGENTS/contrato.md` (§7.3), la primera prueba de integración incremental del pipeline de Glue se realiza sobre la tabla **`genre`** (columna de control `updated_at` mantenida por el trigger `trg_genre_set_updated_at`).

### Paso 1 — Verificar el trigger y crear el registro de prueba

En la EC2 (`python manage.py shell`):

```python
from django.db import connection
from tracks.models import Genre

with connection.cursor() as cur:
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'genre'
        ORDER BY ordinal_position;
    """)
    print("Columnas:", cur.fetchall())

    cur.execute("""
        SELECT tgname
        FROM pg_trigger
        WHERE tgrelid = 'public.genre'::regclass AND NOT tgisinternal;
    """)
    print("Triggers:", cur.fetchall())

g, created = Genre.objects.get_or_create(name="zz_incremental_test")
print(f"TABLA: genre\nID: {g.id}\nupdated_at (antes): {g.updated_at.isoformat()}")
```

Entregar a Juanc los tres datos (`TABLA: genre`, `ID`, `updated_at (antes)`) y **esperar** a que confirme su primera extracción en Glue (Checkpoint **CP-F**).

### Paso 2 — Modificar el registro tras la primera extracción de Juanc

Una vez Juanc confirme la primera corrida:

```python
from tracks.models import Genre

g = Genre.objects.get(name="zz_incremental_test")
antes = g.updated_at
g.name = "zz_incremental_test_v2"
g.save()
g.refresh_from_db()
print(f"ID: {g.id}")
print(f"updated_at (antes):   {antes.isoformat()}")
print(f"updated_at (después): {g.updated_at.isoformat()}")
assert g.updated_at > antes, "El trigger trg_genre_set_updated_at no avanzó updated_at"
```

Avisar a Juanc para que ejecute la segunda extracción incremental (`WHERE updated_at > last_value`), la cual debe capturar únicamente la fila modificada. No eliminar el registro de prueba hasta que el equipo cierre la verificación.

---

## Verificación del contrato ER en desarrollo

Para comprobar localmente que `database/schema.sql` y el diagrama Mermaid de `AGENTS/contrato.md` están sincronizados:

```bash
python database/check_contract_er.py
```
