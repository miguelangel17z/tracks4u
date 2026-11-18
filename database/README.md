# Base de Datos de Tracks4U (`database/`)

Esta carpeta contiene la definición del esquema relacional en PostgreSQL (Amazon RDS), los datos iniciales, la actualización de metadatos multimedia hacia S3 y los scripts de permisos y verificación.

---

## 1. Archivos

| Archivo | Propósito |
|---|---|
| `schema.sql` | **Fuente de verdad del esquema.** Crea las 12 tablas (`"user"`, `artist`, `genre`, `artist_genre`, `track`, `track_genre`, `playlist`, `playlist_track`, `"order"`, `order_item`, `telemetry_event`, `etl_watermark`), `CHECK` constraints, índices, la función `set_updated_at()`, los 8 triggers `trg_<tabla>_set_updated_at` y el catálogo inicial de 20 géneros. Es idempotente (`IF NOT EXISTS`). |
| `seed.sql` | Datos iniciales idempotentes: 6 usuarios, 14 artistas con sus géneros, 36 canciones base, 3 playlists y las filas iniciales de `etl_watermark`. |
| `seed_media_updates.sql` | Actualiza las 36 canciones del seed con sus títulos completos corregidos, duración en segundos (`duration_sec`), precios, BPM, idioma, keys de S3 (`audio/<artist_id>/<uuid>.opus` y `covers/tracks/<uuid>.<ext>`) y relaciones en `track_genre`. |
| `check_contract_er.py` | Verifica con `pglast` que el diagrama entidad-relación de `AGENTS/contrato.md` coincida columna por columna con `schema.sql`. |
| `rds/grants.sql` | Script `psql` idempotente que configura los privilegios del rol de la aplicación (`app_user`) y del rol de ingesta de Glue (`ingest_user`). |
| `rds/verify.sql` | Script `psql` que valida la existencia de las 12 tablas, los 8 triggers `trg_*_set_updated_at`, los >= 20 géneros y los permisos del rol de ingesta. |

---

## 2. Orden de Ejecución en RDS (desde la EC2)

Variables de conexión de RDS:
- **Host:** `tracks4u-postgres-dev.c4qkjciamuny.us-east-1.rds.amazonaws.com`
- **Puerto:** `5432`
- **Base de datos:** `tracks4u`
- **Usuario dueño / aplicación:** `tracks4u_app`
- **SSL:** `PGSSLMODE=require`

### Paso 1 — Aplicar esquema y migraciones de Django
Desde `tracks4u/`:

```bash
cd ~/tracks4uProject/tracks4u
source ../.venv/bin/activate
python manage.py migrate
```
*(La migración `core.0001_schema` ejecuta automáticamente `database/schema.sql` dentro de RDS y crea las tablas internas de Django).*

### Paso 2 — Cargar el seed inicial
```bash
cd ~/tracks4uProject
PGSSLMODE=require psql \
  -h tracks4u-postgres-dev.c4qkjciamuny.us-east-1.rds.amazonaws.com \
  -p 5432 -U tracks4u_app -d tracks4u \
  -f database/seed.sql
```

### Paso 3 — Subir las 36 canciones y 33 portadas a S3 y actualizar metadatos en RDS
```bash
cd ~/tracks4uProject/tracks4u
source ../.venv/bin/activate
python manage.py sync_seed_media
```
*(O si solo deseas aplicar los metadatos en RDS vía SQL: `PGSSLMODE=require psql -h ... -U tracks4u_app -d tracks4u -f database/seed_media_updates.sql`).*

### Paso 4 — Aplicar permisos (`grants.sql`) y verificar (`verify.sql`)
Si cuentan con un rol separado para Glue (`<INGEST_ROLE>`):

```bash
cd ~/tracks4uProject
PGSSLMODE=require psql \
  -h tracks4u-postgres-dev.c4qkjciamuny.us-east-1.rds.amazonaws.com \
  -p 5432 -U tracks4u_app -d tracks4u \
  -v db_name=tracks4u \
  -v owner_user=tracks4u_app \
  -v app_user=tracks4u_app \
  -v ingest_user=<INGEST_ROLE> \
  -f database/rds/grants.sql

PGSSLMODE=require psql \
  -h tracks4u-postgres-dev.c4qkjciamuny.us-east-1.rds.amazonaws.com \
  -p 5432 -U tracks4u_app -d tracks4u \
  -v ingest_user=<INGEST_ROLE> \
  -f database/rds/verify.sql
```

Si ejecutan `verify.sql` sin rol de ingesta separado (solo verificando tablas, triggers y catálogo):
```bash
PGSSLMODE=require psql \
  -h tracks4u-postgres-dev.c4qkjciamuny.us-east-1.rds.amazonaws.com \
  -p 5432 -U tracks4u_app -d tracks4u \
  -f database/rds/verify.sql
```
