-- Tracks4U - Verificación post-despliegue en RDS PostgreSQL (T6)
-- Fuente de diseño: AGENTS/tasks.md (T6) y AGENTS/design.md §3.5, §6.2
--
-- Uso:
--   1) Verificar esquema, triggers y catálogo base:
--      PGSSLMODE=require psql -h <RDS_HOST> -U tracks4u_app -d tracks4u -f database/rds/verify.sql
--
--   2) Verificar además los privilegios del rol de ingesta:
--      PGSSLMODE=require psql -h <RDS_HOST> -U tracks4u_app -d tracks4u \
--        -v ingest_user=<rol_ingesta> -f database/rds/verify.sql

\set ON_ERROR_STOP on

DO $$
DECLARE
    v_expected_tables text[] := ARRAY[
        'user',
        'artist',
        'genre',
        'artist_genre',
        'track',
        'track_genre',
        'playlist',
        'playlist_track',
        'order',
        'order_item',
        'telemetry_event',
        'etl_watermark'
    ];
    v_expected_triggers text[] := ARRAY[
        'trg_user_set_updated_at',
        'trg_artist_set_updated_at',
        'trg_genre_set_updated_at',
        'trg_track_set_updated_at',
        'trg_playlist_set_updated_at',
        'trg_playlist_track_set_updated_at',
        'trg_order_set_updated_at',
        'trg_order_item_set_updated_at'
    ];
    v_item text;
    v_exists boolean;
    v_genre_count bigint;
BEGIN
    -- 1. Comprobar que existen las 12 tablas del esquema en public
    FOREACH v_item IN ARRAY v_expected_tables LOOP
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = v_item
        ) INTO v_exists;

        IF NOT v_exists THEN
            RAISE EXCEPTION 'Verificación fallida: falta la tabla public.%', quote_ident(v_item);
        END IF;
    END LOOP;

    -- 2. Comprobar que existen los 8 triggers trg_<tabla>_set_updated_at
    FOREACH v_item IN ARRAY v_expected_triggers LOOP
        SELECT EXISTS (
            SELECT 1
            FROM pg_trigger t
            JOIN pg_class c ON c.oid = t.tgrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND t.tgname = v_item
              AND NOT t.tgisinternal
        ) INTO v_exists;

        IF NOT v_exists THEN
            RAISE EXCEPTION 'Verificación fallida: falta el trigger %', v_item;
        END IF;
    END LOOP;

    -- 3. Comprobar que el catálogo genre tiene al menos los 20 géneros iniciales
    SELECT COUNT(*) INTO v_genre_count FROM public.genre;
    IF v_genre_count < 20 THEN
        RAISE EXCEPTION 'Verificación fallida: genre tiene % filas (se esperaban >= 20)', v_genre_count;
    END IF;

    RAISE NOTICE 'OK: 12 tablas, 8 triggers updated_at y catálogo genre (% filas) verificados.', v_genre_count;
END;
$$;

-- 4. Si se definió -v ingest_user=..., verificar su superficie de permisos (design.md §6.2)
\if :{?ingest_user}
SET SESSION "tracks4u.ingest_user" = :'ingest_user';

DO $$
DECLARE
    v_role text := current_setting('tracks4u.ingest_user', true);
    v_has_django_session boolean;
BEGIN
    IF v_role IS NULL OR btrim(v_role) = '' THEN
        RAISE EXCEPTION 'Verificación fallida: ingest_user está vacío';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_role) THEN
        RAISE EXCEPTION 'Verificación fallida: el rol % no existe en pg_roles', v_role;
    END IF;

    -- Permisos positivos obligatorios
    IF NOT has_table_privilege(v_role, 'public.track', 'SELECT') THEN
        RAISE EXCEPTION 'Verificación fallida: % no tiene SELECT en track', v_role;
    END IF;

    IF NOT has_table_privilege(v_role, 'public.etl_watermark', 'SELECT')
       OR NOT has_table_privilege(v_role, 'public.etl_watermark', 'INSERT')
       OR NOT has_table_privilege(v_role, 'public.etl_watermark', 'UPDATE') THEN
        RAISE EXCEPTION 'Verificación fallida: % debe tener SELECT, INSERT y UPDATE en etl_watermark', v_role;
    END IF;

    IF NOT has_column_privilege(v_role, 'public."user"', 'username', 'SELECT') THEN
        RAISE EXCEPTION 'Verificación fallida: % no tiene SELECT sobre "user"(username)', v_role;
    END IF;

    -- Restricciones negativas obligatorias (seguridad / aislamiento del outbox y PII)
    IF has_table_privilege(v_role, 'public.telemetry_event', 'SELECT') THEN
        RAISE EXCEPTION 'Verificación fallida: % NO debe tener SELECT en telemetry_event', v_role;
    END IF;

    IF has_column_privilege(v_role, 'public."user"', 'email', 'SELECT') THEN
        RAISE EXCEPTION 'Verificación fallida: % NO debe tener SELECT sobre "user"(email)', v_role;
    END IF;

    IF has_column_privilege(v_role, 'public."user"', 'password', 'SELECT') THEN
        RAISE EXCEPTION 'Verificación fallida: % NO debe tener SELECT sobre "user"(password)', v_role;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'django_session'
    ) INTO v_has_django_session;

    IF v_has_django_session AND has_table_privilege(v_role, 'public.django_session', 'SELECT') THEN
        RAISE EXCEPTION 'Verificación fallida: % NO debe tener SELECT en django_session', v_role;
    END IF;

    RAISE NOTICE 'OK: superficie de privilegios verificada para ingest_user=%', v_role;
END;
$$;
\endif
