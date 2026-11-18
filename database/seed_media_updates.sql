-- Tracks4U - Actualización idempotente de metadatos, duraciones, géneros y keys S3 (36 tracks)
-- Generado automáticamente por: python manage.py sync_seed_media --export-sql
-- Requiere haber aplicado previamente database/schema.sql y database/seed.sql.

BEGIN;

-- Track 1: 2/Catorce (206s)
UPDATE track SET artist_id = 10, title = '2/Catorce', subgenre = 'R&B Urbano', language = 'es', mood_tags = ARRAY['romantic', 'chill']::TEXT[], bpm = 98, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/10/8de1219e189056f2aa36eda37e0f1c58.opus', cover_image = 'covers/tracks/8de1219e189056f2aa36eda37e0f1c58.webp', duration_sec = 206 WHERE id = 1;
INSERT INTO track_genre (track_id, genre_id) SELECT 1, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'R&B') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 2: 4x4 (203s)
UPDATE track SET artist_id = 3, title = '4x4', subgenre = 'Southern Trap', language = 'en', mood_tags = ARRAY['hype', 'energetic']::TEXT[], bpm = 140, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/3/94be47c8618757ba9973f1b51e2f30c5.opus', cover_image = NULL, duration_sec = 203 WHERE id = 2;
INSERT INTO track_genre (track_id, genre_id) SELECT 2, g.id FROM genre g WHERE g.name IN ('Hip-Hop', 'Trap') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 3: 18 (131s)
UPDATE track SET artist_id = 1, title = '18', subgenre = 'Trap Urbano', language = 'es', mood_tags = ARRAY['urban', 'night']::TEXT[], bpm = 124, track_type = 'ORIGINAL', price = 1.49, audio_file = 'audio/1/2a55bac0322c5f0abcef69a8fae3225a.opus', cover_image = 'covers/tracks/2a55bac0322c5f0abcef69a8fae3225a.webp', duration_sec = 131 WHERE id = 3;
INSERT INTO track_genre (track_id, genre_id) SELECT 3, g.id FROM genre g WHERE g.name IN ('Latin Trap', 'Reggaeton') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 4: 327 (feat. Tyler, The Creator & Billie Essco) (349s)
UPDATE track SET artist_id = 4, title = '327 (feat. Tyler, The Creator & Billie Essco)', subgenre = 'Jazz Rap', language = 'en', mood_tags = ARRAY['chill', 'smooth']::TEXT[], bpm = 84, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/4/e1b6771fdccb5e76827c428ddaa96aaa.opus', cover_image = 'covers/tracks/e1b6771fdccb5e76827c428ddaa96aaa.jpg', duration_sec = 349 WHERE id = 4;
INSERT INTO track_genre (track_id, genre_id) SELECT 4, g.id FROM genre g WHERE g.name IN ('Hip-Hop', 'Alternative Hip-Hop', 'Jazz') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 5: 444 (175s)
UPDATE track SET artist_id = 1, title = '444', subgenre = 'Trap Latino', language = 'es', mood_tags = ARRAY['dark', 'urban']::TEXT[], bpm = 130, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/1/79965e38c8815292a8f948b3bf53b696.opus', cover_image = 'covers/tracks/79965e38c8815292a8f948b3bf53b696.webp', duration_sec = 175 WHERE id = 5;
INSERT INTO track_genre (track_id, genre_id) SELECT 5, g.id FROM genre g WHERE g.name IN ('Latin Trap', 'Reggaeton') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 6: 90210 (339s)
UPDATE track SET artist_id = 3, title = '90210', subgenre = 'Psychedelic Trap', language = 'en', mood_tags = ARRAY['atmospheric', 'melodic']::TEXT[], bpm = 118, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/3/0772e9792fe55ac2985244cb3705b4f5.opus', cover_image = 'covers/tracks/0772e9792fe55ac2985244cb3705b4f5.webp', duration_sec = 339 WHERE id = 6;
INSERT INTO track_genre (track_id, genre_id) SELECT 6, g.id FROM genre g WHERE g.name IN ('Hip-Hop', 'Trap') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 7: A BOY IS A GUN* (234s)
UPDATE track SET artist_id = 4, title = 'A BOY IS A GUN*', subgenre = 'Neo-Soul Rap', language = 'en', mood_tags = ARRAY['soulful', 'melancholic']::TEXT[], bpm = 89, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/4/4c9b89408cc5594c892ebcf718981e9b.opus', cover_image = 'covers/tracks/4c9b89408cc5594c892ebcf718981e9b.png', duration_sec = 234 WHERE id = 7;
INSERT INTO track_genre (track_id, genre_id) SELECT 7, g.id FROM genre g WHERE g.name IN ('Hip-Hop', 'Alternative Hip-Hop', 'R&B') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 8: L$D (329s)
UPDATE track SET artist_id = 2, title = 'L$D', subgenre = 'Experimental Rap', language = 'en', mood_tags = ARRAY['psychedelic', 'dreamy']::TEXT[], bpm = 120, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/2/85acbe7dca805fbaa3ceda1522780321.opus', cover_image = 'covers/tracks/85acbe7dca805fbaa3ceda1522780321.png', duration_sec = 329 WHERE id = 8;
INSERT INTO track_genre (track_id, genre_id) SELECT 8, g.id FROM genre g WHERE g.name IN ('Hip-Hop', 'Rap') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 9: Praise the Lord (Da Shine) (feat. Skepta) (227s)
UPDATE track SET artist_id = 2, title = 'Praise the Lord (Da Shine) (feat. Skepta)', subgenre = 'Experimental Rap', language = 'en', mood_tags = ARRAY['hype', 'confident']::TEXT[], bpm = 80, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/2/7a84f1d958435473bc4e7e7826152551.opus', cover_image = 'covers/tracks/7a84f1d958435473bc4e7e7826152551.jpeg', duration_sec = 227 WHERE id = 9;
INSERT INTO track_genre (track_id, genre_id) SELECT 9, g.id FROM genre g WHERE g.name IN ('Hip-Hop', 'Rap', 'Grime') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 10: AURORA (193s)
UPDATE track SET artist_id = 1, title = 'AURORA', subgenre = 'Reggaeton Melódico', language = 'es', mood_tags = ARRAY['melodic', 'night']::TEXT[], bpm = 95, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/1/4391b10d4d225e7d86b0c48ec9f2803a.opus', cover_image = 'covers/tracks/4391b10d4d225e7d86b0c48ec9f2803a.webp', duration_sec = 193 WHERE id = 10;
INSERT INTO track_genre (track_id, genre_id) SELECT 10, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 11: 120 (151s)
UPDATE track SET artist_id = 5, title = '120', subgenre = 'Latin Trap', language = 'es', mood_tags = ARRAY['melancholic', 'chill']::TEXT[], bpm = 120, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/5/1f6d762723a35a7e8c50cef561682436.opus', cover_image = NULL, duration_sec = 151 WHERE id = 11;
INSERT INTO track_genre (track_id, genre_id) SELECT 11, g.id FROM genre g WHERE g.name IN ('Latin Trap', 'Trap') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 12: GRACIAS POR NADA (176s)
UPDATE track SET artist_id = 5, title = 'GRACIAS POR NADA', subgenre = 'Latin Trap', language = 'es', mood_tags = ARRAY['introspective', 'urban']::TEXT[], bpm = 136, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/5/a4de33c91d6d58c0bcc425adf5a661ca.opus', cover_image = 'covers/tracks/a4de33c91d6d58c0bcc425adf5a661ca.webp', duration_sec = 176 WHERE id = 12;
INSERT INTO track_genre (track_id, genre_id) SELECT 12, g.id FROM genre g WHERE g.name IN ('Latin Trap', 'Reggaeton') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 13: KLOuFRENS (201s)
UPDATE track SET artist_id = 5, title = 'KLOuFRENS', subgenre = 'Perreo', language = 'es', mood_tags = ARRAY['party', 'dance']::TEXT[], bpm = 96, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/5/75e8a2f5a24e57f7a37fcf9681faa1c7.opus', cover_image = 'covers/tracks/75e8a2f5a24e57f7a37fcf9681faa1c7.webp', duration_sec = 201 WHERE id = 13;
INSERT INTO track_genre (track_id, genre_id) SELECT 13, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 14: LA DIFÍCIL (192s)
UPDATE track SET artist_id = 5, title = 'LA DIFÍCIL', subgenre = 'Reggaeton Clásico', language = 'es', mood_tags = ARRAY['party', 'energetic']::TEXT[], bpm = 90, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/5/671d32e146c854e0a0b2714bd018969a.opus', cover_image = 'covers/tracks/671d32e146c854e0a0b2714bd018969a.webp', duration_sec = 192 WHERE id = 14;
INSERT INTO track_genre (track_id, genre_id) SELECT 14, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 15: LA MuDANZA (215s)
UPDATE track SET artist_id = 5, title = 'LA MuDANZA', subgenre = 'Salsa Urbana', language = 'es', mood_tags = ARRAY['upbeat', 'roots']::TEXT[], bpm = 105, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/5/a29e7a588b015ba4b0a223c998e8da3f.opus', cover_image = 'covers/tracks/a29e7a588b015ba4b0a223c998e8da3f.webp', duration_sec = 215 WHERE id = 15;
INSERT INTO track_genre (track_id, genre_id) SELECT 15, g.id FROM genre g WHERE g.name IN ('Salsa', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 16: LO QUE LE PASÓ A HAWAii (230s)
UPDATE track SET artist_id = 5, title = 'LO QUE LE PASÓ A HAWAii', subgenre = 'Jíbaro / Urbano', language = 'es', mood_tags = ARRAY['reflective', 'acoustic']::TEXT[], bpm = 88, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/5/1b71f562b2d256c1b8cf886b33cf0c3a.opus', cover_image = 'covers/tracks/1b71f562b2d256c1b8cf886b33cf0c3a.webp', duration_sec = 230 WHERE id = 16;
INSERT INTO track_genre (track_id, genre_id) SELECT 16, g.id FROM genre g WHERE g.name IN ('Latin', 'Alternative Hip-Hop') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 17: MONACO (440s)
UPDATE track SET artist_id = 5, title = 'MONACO', subgenre = 'Orchestral Trap', language = 'es', mood_tags = ARRAY['luxury', 'confident']::TEXT[], bpm = 139, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/5/0880ec49cb155033b230b46af85c9abb.opus', cover_image = 'covers/tracks/0880ec49cb155033b230b46af85c9abb.webp', duration_sec = 440 WHERE id = 17;
INSERT INTO track_genre (track_id, genre_id) SELECT 17, g.id FROM genre g WHERE g.name IN ('Latin Trap', 'Hip-Hop') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 18: PIToRRO DE COCO (236s)
UPDATE track SET artist_id = 5, title = 'PIToRRO DE COCO', subgenre = 'Plena / Jíbaro', language = 'es', mood_tags = ARRAY['nostalgic', 'festive']::TEXT[], bpm = 98, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/5/1bcb8b62b3e4564fb7726cce41cbf468.opus', cover_image = 'covers/tracks/1bcb8b62b3e4564fb7726cce41cbf468.webp', duration_sec = 236 WHERE id = 18;
INSERT INTO track_genre (track_id, genre_id) SELECT 18, g.id FROM genre g WHERE g.name IN ('Latin', 'Reggaeton') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 19: ACHO PR (feat. Arcángel, De La Ghetto, Ñengo Flow) (360s)
UPDATE track SET artist_id = 5, title = 'ACHO PR (feat. Arcángel, De La Ghetto, Ñengo Flow)', subgenre = 'Malianteo', language = 'es', mood_tags = ARRAY['intense', 'street']::TEXT[], bpm = 145, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/5/4727d4abef0658af82c6b903236467fe.opus', cover_image = NULL, duration_sec = 360 WHERE id = 19;
INSERT INTO track_genre (track_id, genre_id) SELECT 19, g.id FROM genre g WHERE g.name IN ('Latin Trap', 'Reggaeton') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 20: BADGYAL (254s)
UPDATE track SET artist_id = 6, title = 'BADGYAL', subgenre = 'Urbano Español', language = 'es', mood_tags = ARRAY['club', 'dance']::TEXT[], bpm = 100, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/6/1f0be3952ff55889bb91ea194a9cd045.opus', cover_image = 'covers/tracks/1f0be3952ff55889bb91ea194a9cd045.webp', duration_sec = 254 WHERE id = 20;
INSERT INTO track_genre (track_id, genre_id) SELECT 20, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Dancehall') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 21: COSAS QUE NO TE DIJE (225s)
UPDATE track SET artist_id = 1, title = 'COSAS QUE NO TE DIJE', subgenre = 'Pop Urbano', language = 'es', mood_tags = ARRAY['romantic', 'melodic']::TEXT[], bpm = 110, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/1/53e16037482c5ec0ac2e635c1d151528.opus', cover_image = 'covers/tracks/53e16037482c5ec0ac2e635c1d151528.webp', duration_sec = 225 WHERE id = 21;
INSERT INTO track_genre (track_id, genre_id) SELECT 21, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Pop') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 22: FDSR (188s)
UPDATE track SET artist_id = 9, title = 'FDSR', subgenre = 'Reggaeton Colombiano', language = 'es', mood_tags = ARRAY['party', 'melodic']::TEXT[], bpm = 96, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/9/70b9349ea30f57d893d459ec865bc1e4.opus', cover_image = 'covers/tracks/70b9349ea30f57d893d459ec865bc1e4.webp', duration_sec = 188 WHERE id = 22;
INSERT INTO track_genre (track_id, genre_id) SELECT 22, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 23: FUMETEO (141s)
UPDATE track SET artist_id = 7, title = 'FUMETEO', subgenre = 'Perreo', language = 'es', mood_tags = ARRAY['energetic', 'club']::TEXT[], bpm = 94, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/7/226de22278165dce9ecf0b34b470d0f2.opus', cover_image = 'covers/tracks/226de22278165dce9ecf0b34b470d0f2.webp', duration_sec = 141 WHERE id = 23;
INSERT INTO track_genre (track_id, genre_id) SELECT 23, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 24: GODIVA (219s)
UPDATE track SET artist_id = 7, title = 'GODIVA', subgenre = 'Reggaeton', language = 'es', mood_tags = ARRAY['night', 'smooth']::TEXT[], bpm = 92, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/7/5f144801389d5f4f98a2570af08bd133.opus', cover_image = 'covers/tracks/5f144801389d5f4f98a2570af08bd133.webp', duration_sec = 219 WHERE id = 24;
INSERT INTO track_genre (track_id, genre_id) SELECT 24, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 25: Julietota (212s)
UPDATE track SET artist_id = 1, title = 'Julietota', subgenre = 'Alt Pop Latino', language = 'es', mood_tags = ARRAY['chill', 'groove']::TEXT[], bpm = 102, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/1/74e20c0095535cd7a282146dca5f4d6e.opus', cover_image = 'covers/tracks/74e20c0095535cd7a282146dca5f4d6e.webp', duration_sec = 212 WHERE id = 25;
INSERT INTO track_genre (track_id, genre_id) SELECT 25, g.id FROM genre g WHERE g.name IN ('Latin', 'Pop', 'R&B') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 26: LA BABY (183s)
UPDATE track SET artist_id = 8, title = 'LA BABY', subgenre = 'Reggaeton', language = 'es', mood_tags = ARRAY['party', 'dance']::TEXT[], bpm = 93, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/8/e509051735cc5d77a1d6cd69d747fffb.opus', cover_image = 'covers/tracks/e509051735cc5d77a1d6cd69d747fffb.webp', duration_sec = 183 WHERE id = 26;
INSERT INTO track_genre (track_id, genre_id) SELECT 26, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 27: MOJABI GHOST (feat. Bad Bunny) (234s)
UPDATE track SET artist_id = 8, title = 'MOJABI GHOST (feat. Bad Bunny)', subgenre = 'Synthwave Urbano', language = 'es', mood_tags = ARRAY['synth', 'night']::TEXT[], bpm = 122, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/8/76f4c2582deb5224ae87f60bde12ddd5.opus', cover_image = 'covers/tracks/76f4c2582deb5224ae87f60bde12ddd5.webp', duration_sec = 234 WHERE id = 27;
INSERT INTO track_genre (track_id, genre_id) SELECT 27, g.id FROM genre g WHERE g.name IN ('Electronic', 'Latin', 'Dance') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 28: Mujeriego (142s)
UPDATE track SET artist_id = 9, title = 'Mujeriego', subgenre = 'Merengue Urbano', language = 'es', mood_tags = ARRAY['festive', 'dance']::TEXT[], bpm = 115, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/9/f13d9753ab6a576eab5069472f3d3a4d.opus', cover_image = 'covers/tracks/f13d9753ab6a576eab5069472f3d3a4d.webp', duration_sec = 142 WHERE id = 28;
INSERT INTO track_genre (track_id, genre_id) SELECT 28, g.id FROM genre g WHERE g.name IN ('Latin', 'Salsa', 'Reggaeton') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 29: Nostálgico (210s)
UPDATE track SET artist_id = 10, title = 'Nostálgico', subgenre = 'UK Garage / Reggaeton', language = 'es', mood_tags = ARRAY['groove', 'nostalgic']::TEXT[], bpm = 98, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/10/cce6128d044d562cb1070472a1f5a306.opus', cover_image = 'covers/tracks/cce6128d044d562cb1070472a1f5a306.webp', duration_sec = 210 WHERE id = 29;
INSERT INTO track_genre (track_id, genre_id) SELECT 29, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Dance', 'R&B') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 30: PARANORMAL (198s)
UPDATE track SET artist_id = 8, title = 'PARANORMAL', subgenre = 'Experimental Reggaeton', language = 'es', mood_tags = ARRAY['atmospheric', 'futuristic']::TEXT[], bpm = 100, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/8/f64c2aa7eadf593b90e9513d02581a9f.opus', cover_image = 'covers/tracks/f64c2aa7eadf593b90e9513d02581a9f.webp', duration_sec = 198 WHERE id = 30;
INSERT INTO track_genre (track_id, genre_id) SELECT 30, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Electronic', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 31: PASIEMPRE (358s)
UPDATE track SET artist_id = 8, title = 'PASIEMPRE', subgenre = 'Experimental Trap', language = 'es', mood_tags = ARRAY['epic', 'intense']::TEXT[], bpm = 118, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/8/83b20828e96d54c286cb4d3d68bb3b79.opus', cover_image = 'covers/tracks/83b20828e96d54c286cb4d3d68bb3b79.webp', duration_sec = 358 WHERE id = 31;
INSERT INTO track_genre (track_id, genre_id) SELECT 31, g.id FROM genre g WHERE g.name IN ('Latin Trap', 'Reggaeton', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 32: AL CALLAO (243s)
UPDATE track SET artist_id = 10, title = 'AL CALLAO', subgenre = 'Reggaeton', language = 'es', mood_tags = ARRAY['sensual', 'night']::TEXT[], bpm = 92, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/10/016022e5605c552998fc2238e38ea6f1.opus', cover_image = 'covers/tracks/016022e5605c552998fc2238e38ea6f1.webp', duration_sec = 243 WHERE id = 32;
INSERT INTO track_genre (track_id, genre_id) SELECT 32, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'R&B') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 33: HOY AQUÍ (188s)
UPDATE track SET artist_id = 10, title = 'HOY AQUÍ', subgenre = 'Synth Reggaeton', language = 'es', mood_tags = ARRAY['upbeat', 'night']::TEXT[], bpm = 116, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/10/7f38b4c2a7415e60b7b94faa7f0dcb2c.opus', cover_image = 'covers/tracks/7f38b4c2a7415e60b7b94faa7f0dcb2c.webp', duration_sec = 188 WHERE id = 33;
INSERT INTO track_genre (track_id, genre_id) SELECT 33, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Pop', 'Electronic') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 34: Espresso Martini (feat. Marconi Impara, Yan Block) (191s)
UPDATE track SET artist_id = 10, title = 'Espresso Martini (feat. Marconi Impara, Yan Block)', subgenre = 'Trap / Reggaeton', language = 'es', mood_tags = ARRAY['club', 'smooth']::TEXT[], bpm = 95, track_type = 'ORIGINAL', price = 1.99, audio_file = 'audio/10/ebbf38d0ee0f52af80d26de17a2bc368.opus', cover_image = 'covers/tracks/ebbf38d0ee0f52af80d26de17a2bc368.webp', duration_sec = 191 WHERE id = 34;
INSERT INTO track_genre (track_id, genre_id) SELECT 34, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin Trap') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 35: REMIX EXCLUSIVO (207s)
UPDATE track SET artist_id = 7, title = 'REMIX EXCLUSIVO', subgenre = 'Perreo', language = 'es', mood_tags = ARRAY['party', 'perreo']::TEXT[], bpm = 94, track_type = 'REMIX', price = 1.99, audio_file = 'audio/7/7ae1ce1297e151e592be51baf6b4669f.opus', cover_image = 'covers/tracks/7ae1ce1297e151e592be51baf6b4669f.webp', duration_sec = 207 WHERE id = 35;
INSERT INTO track_genre (track_id, genre_id) SELECT 35, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin') ON CONFLICT (track_id, genre_id) DO NOTHING;

-- Track 36: UN TRÍO (168s)
UPDATE track SET artist_id = 9, title = 'UN TRÍO', subgenre = 'Reggaeton', language = 'es', mood_tags = ARRAY['party', 'urban']::TEXT[], bpm = 96, track_type = 'ORIGINAL', price = 2.49, audio_file = 'audio/9/7a2bc4a0295a57faa2b3cf92451a7854.opus', cover_image = 'covers/tracks/7a2bc4a0295a57faa2b3cf92451a7854.webp', duration_sec = 168 WHERE id = 36;
INSERT INTO track_genre (track_id, genre_id) SELECT 36, g.id FROM genre g WHERE g.name IN ('Reggaeton', 'Latin', 'Regional Mexican') ON CONFLICT (track_id, genre_id) DO NOTHING;

COMMIT;
