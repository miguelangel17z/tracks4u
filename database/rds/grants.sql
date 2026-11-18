-- Tracks4U - Permisos en Amazon RDS PostgreSQL (T6)
-- Fuente de diseño: AGENTS/design.md §6 y AGENTS/contrato.md §5-§7
--
-- Uso (desde la EC2, ejecutado con el usuario dueño del esquema):
--   PGSSLMODE=require psql \
--     -h tracks4u-postgres-dev.c4qkjciamuny.us-east-1.rds.amazonaws.com \
--     -p 5432 -U tracks4u_app -d tracks4u \
--     -v db_name=tracks4u \
--     -v owner_user=tracks4u_app \
--     -v app_user=tracks4u_app \
--     -v ingest_user=<rol_de_ingesta_glue> \
--     -f database/rds/grants.sql
--
-- Script idempotente. Se debe re-ejecutar tras cualquier cambio de esquema.

\set ON_ERROR_STOP on

\if :{?db_name}
\else
\echo 'ERROR: Falta -v db_name=<nombre_bd>'
\quit 1
\endif

\if :{?owner_user}
\else
\echo 'ERROR: Falta -v owner_user=<rol_dueno>'
\quit 1
\endif

\if :{?app_user}
\else
\echo 'ERROR: Falta -v app_user=<rol_app>'
\quit 1
\endif

\if :{?ingest_user}
\else
\echo 'ERROR: Falta -v ingest_user=<rol_ingesta>'
\quit 1
\endif

BEGIN;

-- ===========================================================================
-- 1. Rol de aplicación (app_user): DML completo sobre el esquema public
-- ===========================================================================
GRANT CONNECT ON DATABASE :"db_name" TO :"app_user";
GRANT USAGE ON SCHEMA public TO :"app_user";

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"app_user";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :"app_user";

ALTER DEFAULT PRIVILEGES FOR ROLE :"owner_user" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app_user";

ALTER DEFAULT PRIVILEGES FOR ROLE :"owner_user" IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO :"app_user";

-- ===========================================================================
-- 2. Rol de ingesta batch/CDC (ingest_user - Glue de Juanc)
--    Superficie restringida según AGENTS/design.md §6.2:
--    - Sin acceso a "user".email, "user".password, "user".app_role, "user".last_login
--    - Sin acceso a telemetry_event ni a tablas internas de Django (django_*, auth_*)
--    - Escritura únicamente en etl_watermark (SELECT, INSERT, UPDATE + secuencia)
--    - Sin ALTER DEFAULT PRIVILEGES (una tabla futura no debe exponerse por defecto)
-- ===========================================================================
GRANT CONNECT ON DATABASE :"db_name" TO :"ingest_user";
GRANT USAGE ON SCHEMA public TO :"ingest_user";

-- Convergencia idempotente: limpia privilegios previos antes de otorgar la superficie exacta
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM :"ingest_user";
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM :"ingest_user";

-- "user": lectura restringida por lista explícita de columnas (sin email, password, app_role, last_login)
GRANT SELECT (
    id,
    username,
    country,
    birth_date,
    gender,
    ethnicity,
    created_at,
    updated_at
) ON TABLE "user" TO :"ingest_user";

-- Tablas de negocio: solo lectura
GRANT SELECT ON TABLE
    artist,
    genre,
    artist_genre,
    track,
    track_genre,
    playlist,
    playlist_track,
    "order",
    order_item
TO :"ingest_user";

-- Control de ingesta incremental: lectura y escritura (sin DELETE)
GRANT SELECT, INSERT, UPDATE ON TABLE etl_watermark TO :"ingest_user";

-- Secuencia de identidad de etl_watermark
GRANT USAGE, SELECT ON SEQUENCE etl_watermark_id_seq TO :"ingest_user";

SET LOCAL "tracks4u.ingest_user" = :'ingest_user';

DO $$
DECLARE
    v_seq  text := pg_get_serial_sequence('etl_watermark', 'id');
    v_role text := current_setting('tracks4u.ingest_user', true);
BEGIN
    IF v_seq IS NOT NULL AND v_role IS NOT NULL AND btrim(v_role) <> '' THEN
        EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO %I', v_seq, v_role);
    END IF;
END;
$$;

COMMIT;
