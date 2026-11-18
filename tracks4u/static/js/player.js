/**
 * Tracks4U — Instrumentación del reproductor <audio> y acciones sociales (AGENTS/tasks.md T7 §7.2).
 *
 * Eventos emitidos (todos los IDs son enteros positivos Number(...)):
 * - play_start    { track_id, playlist_id? }
 * - play_progress { track_id, position_sec, percent_listened } (cada 15 s y al pausar)
 * - pause         { track_id, position_sec }
 * - resume        { track_id, position_sec }
 * - seek          { track_id, from_sec, to_sec }
 * - play_complete { track_id, seconds_listened }
 * - skip          { track_id, position_sec, percent_listened }
 * - like / unlike { track_id }
 * - follow / unfollow { artist_id }
 * - share         { track_id, channel }
 */
(function () {
    "use strict";

    var PROGRESS_INTERVAL_MS = 15000;
    var activeAudio = null;

    function toPositiveInt(value) {
        var n = Number(value);
        return Number.isInteger(n) && n > 0 ? n : null;
    }

    function clampPercent(positionSec, durationSec) {
        if (!durationSec || !isFinite(durationSec) || durationSec <= 0) {
            return 0;
        }
        var pct = Math.round((positionSec / durationSec) * 100);
        return Math.max(0, Math.min(100, pct));
    }

    function emit(eventType, payload) {
        if (window.Telemetry && typeof window.Telemetry.track === "function") {
            window.Telemetry.track(eventType, payload);
        }
    }

    function bindAudioElement(audioEl) {
        if (!audioEl || audioEl.dataset.t4uBound === "1") {
            return;
        }
        var trackId = toPositiveInt(audioEl.dataset.trackId);
        if (!trackId) {
            return;
        }
        audioEl.dataset.t4uBound = "1";

        var state = {
            trackId: trackId,
            playlistId: toPositiveInt(audioEl.dataset.playlistId),
            hasStarted: false,
            completed: false,
            seekingFromSec: null,
            lastKnownPositionSec: 0,
            progressTimer: null,
        };

        function clearProgressTimer() {
            if (state.progressTimer) {
                clearInterval(state.progressTimer);
                state.progressTimer = null;
            }
        }

        function emitProgress() {
            var pos = Math.max(0, Math.round(audioEl.currentTime || 0));
            var pct = clampPercent(audioEl.currentTime || 0, audioEl.duration || 0);
            emit("play_progress", {
                track_id: state.trackId,
                position_sec: pos,
                percent_listened: pct,
            });
        }

        function startProgressTimer() {
            clearProgressTimer();
            state.progressTimer = setInterval(function () {
                if (!audioEl.paused && !audioEl.ended) {
                    emitProgress();
                }
            }, PROGRESS_INTERVAL_MS);
        }

        audioEl._t4uEmitSkipAndStop = function () {
            clearProgressTimer();
            if (state.hasStarted && !state.completed && !audioEl.ended) {
                var pos = Math.max(0, Math.round(audioEl.currentTime || 0));
                var pct = clampPercent(audioEl.currentTime || 0, audioEl.duration || 0);
                emit("skip", {
                    track_id: state.trackId,
                    position_sec: pos,
                    percent_listened: pct,
                });
            }
            state.hasStarted = false;
            state.completed = false;
            if (!audioEl.paused) {
                audioEl._t4uSuppressPauseEvent = true;
                audioEl.pause();
            }
        };

        audioEl.addEventListener("timeupdate", function () {
            if (!audioEl.seeking) {
                state.lastKnownPositionSec = Math.max(0, Math.round(audioEl.currentTime || 0));
            }
        });

        audioEl.addEventListener("play", function () {
            if (activeAudio && activeAudio !== audioEl && typeof activeAudio._t4uEmitSkipAndStop === "function") {
                activeAudio._t4uEmitSkipAndStop();
            }
            activeAudio = audioEl;

            if (!state.hasStarted || state.completed) {
                state.hasStarted = true;
                state.completed = false;
                var startPayload = { track_id: state.trackId };
                var plId = toPositiveInt(audioEl.dataset.playlistId) || state.playlistId;
                if (plId) {
                    startPayload.playlist_id = plId;
                }
                emit("play_start", startPayload);
            } else {
                emit("resume", {
                    track_id: state.trackId,
                    position_sec: Math.max(0, Math.round(audioEl.currentTime || 0)),
                });
            }
            startProgressTimer();
        });

        audioEl.addEventListener("pause", function () {
            clearProgressTimer();
            if (audioEl._t4uSuppressPauseEvent) {
                audioEl._t4uSuppressPauseEvent = false;
                return;
            }
            if (audioEl.ended || state.completed) {
                return;
            }
            var pos = Math.max(0, Math.round(audioEl.currentTime || 0));
            emitProgress();
            emit("pause", {
                track_id: state.trackId,
                position_sec: pos,
            });
        });

        audioEl.addEventListener("seeking", function () {
            if (state.seekingFromSec === null) {
                state.seekingFromSec = state.lastKnownPositionSec;
            }
        });

        audioEl.addEventListener("seeked", function () {
            var fromSec = state.seekingFromSec !== null ? state.seekingFromSec : state.lastKnownPositionSec;
            var toSec = Math.max(0, Math.round(audioEl.currentTime || 0));
            state.seekingFromSec = null;
            state.lastKnownPositionSec = toSec;
            if (Math.abs(toSec - fromSec) >= 2) {
                emit("seek", {
                    track_id: state.trackId,
                    from_sec: fromSec,
                    to_sec: toSec,
                });
            }
        });

        audioEl.addEventListener("ended", function () {
            clearProgressTimer();
            state.completed = true;
            state.hasStarted = false;
            var listened = Math.max(
                1,
                Math.round(audioEl.duration || audioEl.currentTime || state.lastKnownPositionSec || 1)
            );
            emit("play_complete", {
                track_id: state.trackId,
                seconds_listened: listened,
            });
            playNextFromElement(audioEl);
        });
    }

    function playNextFromElement(currentEl) {
        var audios = Array.prototype.slice.call(document.querySelectorAll("audio.t4u-audio"));
        var idx = audios.indexOf(currentEl);
        if (idx >= 0 && idx + 1 < audios.length) {
            var nextAudio = audios[idx + 1];
            nextAudio.currentTime = 0;
            nextAudio.play().catch(function () {});
        }
    }

    function skipCurrent() {
        var audios = Array.prototype.slice.call(document.querySelectorAll("audio.t4u-audio"));
        if (!audios.length) {
            return;
        }
        var current = activeAudio || audios[0];
        if (current && typeof current._t4uEmitSkipAndStop === "function") {
            current._t4uEmitSkipAndStop();
            current.currentTime = 0;
        }
        var idx = audios.indexOf(current);
        var nextIdx = idx >= 0 && idx + 1 < audios.length ? idx + 1 : 0;
        if (audios[nextIdx]) {
            audios[nextIdx].currentTime = 0;
            audios[nextIdx].play().catch(function () {});
        }
    }

    function toggleLike(trackId, btnEl) {
        var id = toPositiveInt(trackId);
        if (!id) {
            return;
        }
        var liked = btnEl && btnEl.dataset.liked === "1";
        var nextLiked = !liked;
        if (btnEl) {
            btnEl.dataset.liked = nextLiked ? "1" : "0";
            btnEl.classList.toggle("text-red-500", nextLiked);
            btnEl.classList.toggle("border-red-600", nextLiked);
        }
        emit(nextLiked ? "like" : "unlike", { track_id: id });
    }

    function toggleFollow(artistId, btnEl) {
        var id = toPositiveInt(artistId);
        if (!id) {
            return;
        }
        var following = btnEl && btnEl.dataset.following === "1";
        var nextFollowing = !following;
        if (btnEl) {
            btnEl.dataset.following = nextFollowing ? "1" : "0";
            btnEl.classList.toggle("bg-red-600", nextFollowing);
            btnEl.classList.toggle("border-red-600", nextFollowing);
            btnEl.textContent = nextFollowing ? "✓ Following" : "+ Follow";
        }
        emit(nextFollowing ? "follow" : "unfollow", { artist_id: id });
    }

    function shareTrack(trackId, channel) {
        var id = toPositiveInt(trackId);
        if (!id) {
            return;
        }
        var ch = channel ? String(channel) : "copy_link";
        emit("share", { track_id: id, channel: ch });
        try {
            var shareUrl = window.location.origin + "/tracks/" + id + "/?ref=external_link";
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(shareUrl);
            }
        } catch (_e) {}
    }

    function bindAll() {
        var elements = document.querySelectorAll("audio.t4u-audio");
        for (var i = 0; i < elements.length; i++) {
            bindAudioElement(elements[i]);
        }
    }

    document.addEventListener("DOMContentLoaded", bindAll);

    window.T4UPlayer = {
        bindAll: bindAll,
        bindAudioElement: bindAudioElement,
        skipCurrent: skipCurrent,
        playNextInPlaylist: skipCurrent,
        toggleLike: toggleLike,
        toggleFollow: toggleFollow,
        shareTrack: shareTrack,
    };
})();
