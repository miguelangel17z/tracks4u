-- Tracks4U - datos iniciales
-- Requiere haber ejecutado antes database/schema.sql (incluye el catalogo de generos).
-- Incluye seis cuentas (cinco usuarios de prueba y sysadmin) y las canciones
-- identificables en los screenshots.
--
-- IMPORTANTE:
-- * Los screenshots muestran nombres truncados por Finder. Los titulos se
--   reconstruyen solo hasta donde el texto visible lo permite.
-- * No se inventan rutas locales, duraciones, BPM, generos de canciones, mood_tags ni precios.
--   audio_file y cover_image quedan NULL hasta mapear los archivos reales.
--   track_genre queda vacia por la misma razon.
-- * Las contrasenas quedan bloqueadas con !RESET_REQUIRED!. El prefijo "!" hace que
--   Django las trate como contrasena inutilizable. Sustituirlas por hashes generados
--   por el backend antes de habilitar login.
-- * country es texto libre con el nombre del pais (p. ej. 'Colombia'), igual que en artist.
-- * El archivo es re-ejecutable: todos los INSERT usan ON CONFLICT DO NOTHING.
-- * etl_watermark se inicializa con una fila por entidad (last_value NULL = primera
--   carga completa). Las actualiza el pipeline de Juanc. ingested_at no existe en las
--   tablas de negocio: lo agrega el pipeline en el lake.

BEGIN;

INSERT INTO "user"
(id, username, email, password, country, birth_date, gender, ethnicity, app_role)
VALUES
(1, 'sysadmin', 'sysadmin@tracks4u.local', '!RESET_REQUIRED!', 'Colombia', '1990-01-01', NULL, NULL, 'sysadmin'),
(2, 'dummy01', 'dummy01@tracks4u.local', '!RESET_REQUIRED!', 'Colombia', '2001-03-12', NULL, NULL, 'user'),
(3, 'dummy02', 'dummy02@tracks4u.local', '!RESET_REQUIRED!', 'Mexico', '1999-07-24', NULL, NULL, 'user'),
(4, 'dummy03', 'dummy03@tracks4u.local', '!RESET_REQUIRED!', 'Argentina', '2002-11-05', NULL, NULL, 'user'),
(5, 'dummy04', 'dummy04@tracks4u.local', '!RESET_REQUIRED!', 'Spain', '1998-02-18', NULL, NULL, 'user'),
(6, 'dummy05', 'dummy05@tracks4u.local', '!RESET_REQUIRED!', 'Colombia', '2000-09-30', NULL, NULL, 'user')
ON CONFLICT DO NOTHING;

INSERT INTO artist (id, stage_name, country) VALUES
(1, 'Unknown Artist', NULL),
(2, 'A$AP Rocky', 'United States'),
(3, 'Travis Scott', 'United States'),
(4, 'Tyler, The Creator', 'United States'),
(5, 'Bad Bunny', 'Puerto Rico'),
(6, 'Bad Gyal', 'Spain'),
(7, 'Feid', 'Colombia'),
(8, 'Tainy', 'Puerto Rico'),
(9, 'Ryan Castro', 'Colombia'),
(10, 'Rauw Alejandro', 'Puerto Rico'),
(11, 'Skepta', 'United Kingdom'),
(12, 'Peso Pluma', 'Mexico'),
(13, 'Jhayco', 'Puerto Rico'),
(14, 'Chris Brown', 'United States')
ON CONFLICT DO NOTHING;

-- Generos de cada artista (antes artist.genres TEXT[]). Se resuelven por nombre contra
-- el catalogo genre. 'Unknown Artist' (id 1) no tiene generos.
INSERT INTO artist_genre (artist_id, genre_id)
SELECT v.artist_id, g.id
FROM (VALUES
    (2, 'Hip-Hop'), (2, 'Rap'),
    (3, 'Hip-Hop'), (3, 'Trap'),
    (4, 'Hip-Hop'), (4, 'Alternative Hip-Hop'),
    (5, 'Reggaeton'), (5, 'Latin Trap'),
    (6, 'Reggaeton'), (6, 'Dancehall'),
    (7, 'Reggaeton'), (7, 'Latin'),
    (8, 'Reggaeton'), (8, 'Latin'),
    (9, 'Reggaeton'), (9, 'Latin'),
    (10, 'Reggaeton'), (10, 'R&B'),
    (11, 'Grime'), (11, 'Hip-Hop'),
    (12, 'Regional Mexican'), (12, 'Latin'),
    (13, 'Reggaeton'), (13, 'Latin'),
    (14, 'R&B'), (14, 'Pop')
) AS v(artist_id, genre_name)
JOIN genre g ON g.name = v.genre_name
ON CONFLICT (artist_id, genre_id) DO NOTHING;

-- IDs explicitos para que las relaciones de ejemplo sean reproducibles.
INSERT INTO track (id, artist_id, title, audio_file, cover_image) VALUES
(1, 1, 'Catorce', NULL, NULL),
(2, 1, '4x4', NULL, NULL),
(3, 1, '18', NULL, NULL),
(4, 1, '327 (feat. Tyler, ... Billie Essco)', NULL, NULL),
(5, 1, '444', NULL, NULL),
(6, 3, '90210', NULL, NULL),
(7, 4, 'A BOY IS A GUN*', NULL, NULL),
(8, 2, 'L$D', NULL, NULL),
(9, 2, 'Praise the Lord (Da Shine) (feat. Skepta)', NULL, NULL),
(10, 1, 'AURORA', NULL, NULL),
(11, 5, '12...', NULL, NULL),
(12, 5, 'GR... (nombre truncado en screenshot)', NULL, NULL),
(13, 5, 'KL... MÁS FOTOS', NULL, NULL),
(14, 5, 'LA... (Video Oficial; nombre truncado)', NULL, NULL),
(15, 5, 'LA... MÁS FOTOS', NULL, NULL),
(16, 5, 'LO... MÁS FOTOS', NULL, NULL),
(17, 5, 'M... (nombre truncado)', NULL, NULL),
(18, 5, 'PIT... MÁS FOTOS', NULL, NULL),
(19, 5, 'BAD BUNNY ft. A... (nslqvapm)', NULL, NULL),
(20, 6, 'BADGYAL', NULL, NULL),
(21, 1, 'COSAS QUE NO TE DIJE', NULL, NULL),
(22, 1, 'FDSR', NULL, NULL),
(23, 7, 'FUMETEO', NULL, NULL),
(24, 1, 'GODIVA', NULL, NULL),
(25, 1, 'Julietota', NULL, NULL),
(26, 8, 'LA BABY', NULL, NULL),
(27, 8, 'MOJABI GHOST (feat. Bad Bunny)', NULL, NULL),
(28, 9, 'Mujeriego', NULL, NULL),
(29, 10, 'Nostálgico', NULL, NULL),
(30, 1, 'PARANORMAL', NULL, NULL),
(31, 8, 'PASIEMPRE', NULL, NULL),
(32, 10, 'Rauw Alejandro - ... (Visualizer)', NULL, NULL),
(33, 10, 'Rauw Alejandro - ...í (Visualizer)', NULL, NULL),
(34, 10, 'Rauw Alejandro - ... (Lyric Video)', NULL, NULL),
(35, 1, 'REMIX EXCLUSIVO', NULL, NULL),
(36, 9, 'Ryan Castro, Peso Pluma - ... (Video Oficial)', NULL, NULL)
ON CONFLICT DO NOTHING;

-- Tres playlists de demostracion pertenecientes a usuarios dummy.
INSERT INTO playlist (id, owner_id, name, description, tags, is_public) VALUES
(1, 2, 'Favoritas', 'Playlist inicial de demostración', ARRAY['favoritas', 'mix'], TRUE),
(2, 3, 'Latin urbano', 'Selección de música urbana latina', ARRAY['latin', 'urbano'], TRUE),
(3, 4, 'Para descubrir', 'Canciones pendientes de clasificar', ARRAY['discovery'], FALSE)
ON CONFLICT DO NOTHING;

INSERT INTO playlist_track (playlist_id, track_id, position) VALUES
(1, 6, 1), (1, 7, 2), (1, 8, 3), (1, 9, 4),
(2, 11, 1), (2, 14, 2), (2, 23, 3), (2, 27, 4), (2, 28, 5), (2, 29, 6),
(3, 1, 1), (3, 2, 2), (3, 3, 3), (3, 21, 4), (3, 35, 5)
-- Objetivo explicito: la restriccion UNIQUE (playlist_id, position) es DEFERRABLE y
-- PostgreSQL no admite restricciones diferidas como arbitro de ON CONFLICT.
ON CONFLICT (playlist_id, track_id) DO NOTHING;

-- Watermarks iniciales. Solo las entidades con updated_at (las tablas puente
-- track_genre / artist_genre y telemetry_event no lo tienen).
INSERT INTO etl_watermark (entity_name, watermark_column, last_value, status) VALUES
('user', 'updated_at', NULL, 'pending'),
('artist', 'updated_at', NULL, 'pending'),
('genre', 'updated_at', NULL, 'pending'),
('track', 'updated_at', NULL, 'pending'),
('playlist', 'updated_at', NULL, 'pending'),
('playlist_track', 'updated_at', NULL, 'pending'),
('order', 'updated_at', NULL, 'pending'),
('order_item', 'updated_at', NULL, 'pending')
ON CONFLICT (entity_name) DO NOTHING;

-- Ajusta las secuencias tras insertar IDs explicitos.
SELECT setval(pg_get_serial_sequence('"user"', 'id'), (SELECT MAX(id) FROM "user"));
SELECT setval(pg_get_serial_sequence('artist', 'id'), (SELECT MAX(id) FROM artist));
SELECT setval(pg_get_serial_sequence('track', 'id'), (SELECT MAX(id) FROM track));
SELECT setval(pg_get_serial_sequence('playlist', 'id'), (SELECT MAX(id) FROM playlist));

COMMIT;
