/**
 * Tracks4U — Cliente de telemetría de comportamiento (AGENTS/design.md §5.3–5.4, tasks.md T7 §7.2).
 *
 * Responsabilidades:
 * - Mantiene session_id (s_<hex>) en sessionStorage.
 * - Detecta device (web_desktop, web_mobile, web_tablet, unknown) y entrypoint
 *   (home, search, artist_profile, playlist, track_page, library, external_link, unknown).
 * - Encola eventos en memoria con event_id UUID v4 y ts ISO 8601 UTC.
 * - Envía lotes a POST /api/events/ cada 5 s o al llegar a 20 eventos, y al salir
 *   (visibilitychange / pagehide) con fetch(..., { keepalive: true }).
 * - Incluye Authorization: Bearer <jwt> si hay sesión, más X-Session-Id, X-Device, X-Entrypoint.
 * - Reintenta una vez ante fallo de red; si vuelve a fallar, descarta sin romper la UI.
 * - Emite automáticamente page_view al cargar y dwell_time al salir.
 */
(function () {
    "use strict";

    var SESSION_STORAGE_KEY = "t4u_session_id";
    var FLUSH_INTERVAL_MS = 5000;
    var FLUSH_THRESHOLD = 20;
    var MAX_BATCH_SIZE = 100;

    var VALID_ENTRYPOINTS = {
        home: true,
        search: true,
        artist_profile: true,
        playlist: true,
        track_page: true,
        library: true,
        external_link: true,
        unknown: true,
    };

    var queue = [];
    var flushTimer = null;
    var pageLoadedAt = Date.now();
    var visibleAccumulatedMs = 0;
    var lastVisibleTimestamp = Date.now();
    var maxScrollPct = 0;
    var dwellSent = false;

    function generateUuidV4() {
        if (window.crypto && typeof window.crypto.randomUUID === "function") {
            return window.crypto.randomUUID();
        }
        return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
            var r = (Math.random() * 16) | 0;
            var v = c === "x" ? r : (r & 0x3) | 0x8;
            return v.toString(16);
        });
    }

    function getOrCreateSessionId() {
        try {
            var existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
            if (existing && /^s_[0-9a-f]+$/i.test(existing)) {
                return existing;
            }
            var cleanHex = generateUuidV4().replace(/-/g, "").slice(0, 24);
            var created = "s_" + cleanHex;
            window.sessionStorage.setItem(SESSION_STORAGE_KEY, created);
            return created;
        } catch (_e) {
            return "s_" + generateUuidV4().replace(/-/g, "").slice(0, 24);
        }
    }

    function detectDevice() {
        try {
            var ua = (navigator.userAgent || "").toLowerCase();
            var isTabletUa = /ipad|tablet|playbook|silk|(android(?!.*mobile))/i.test(ua);
            var isMobileUa = /iphone|ipod|android.*mobile|windows phone|blackberry/i.test(ua);

            if (isTabletUa) {
                return "web_tablet";
            }
            if (isMobileUa) {
                return "web_mobile";
            }
            if (window.matchMedia) {
                if (window.matchMedia("(max-width: 640px)").matches) {
                    return "web_mobile";
                }
                if (window.matchMedia("(max-width: 1024px) and (pointer: coarse)").matches) {
                    return "web_tablet";
                }
            }
            return "web_desktop";
        } catch (_e) {
            return "unknown";
        }
    }

    function detectEntrypoint() {
        try {
            var params = new URLSearchParams(window.location.search || "");
            var refParam = (params.get("ref") || "").trim().toLowerCase();
            if (refParam && VALID_ENTRYPOINTS[refParam]) {
                return refParam;
            }
            var bodyEntry =
                document.body && document.body.dataset && document.body.dataset.entrypoint
                    ? document.body.dataset.entrypoint.trim().toLowerCase()
                    : "";
            if (bodyEntry && VALID_ENTRYPOINTS[bodyEntry]) {
                return bodyEntry;
            }
        } catch (_e) {}
        return "unknown";
    }

    function detectCurrentView() {
        if (document.body && document.body.dataset && document.body.dataset.view) {
            return document.body.dataset.view.trim();
        }
        return "unknown";
    }

    var sessionId = getOrCreateSessionId();
    var device = detectDevice();

    function getContextHeaders() {
        var entrypoint = detectEntrypoint();
        var headers = {
            "X-Session-Id": sessionId,
            "X-Device": device,
            "X-Entrypoint": entrypoint,
        };
        try {
            var token = window.localStorage.getItem("token");
            if (token) {
                headers["Authorization"] = "Bearer " + token;
            }
        } catch (_e) {}
        return headers;
    }

    function computeScrollPct() {
        try {
            var doc = document.documentElement;
            var body = document.body;
            var scrollTop = window.pageYOffset || doc.scrollTop || body.scrollTop || 0;
            var viewportHeight = window.innerHeight || doc.clientHeight || 0;
            var fullHeight = Math.max(
                body.scrollHeight || 0,
                doc.scrollHeight || 0,
                body.offsetHeight || 0,
                doc.offsetHeight || 0,
                1
            );
            if (fullHeight <= viewportHeight) {
                return 100;
            }
            var pct = Math.round(((scrollTop + viewportHeight) / fullHeight) * 100);
            return Math.max(0, Math.min(100, pct));
        } catch (_e) {
            return 0;
        }
    }

    function sendBatch(batch, useKeepalive, isRetry) {
        if (!batch || !batch.length) {
            return;
        }
        var headers = getContextHeaders();
        headers["Content-Type"] = "application/json";

        var body = JSON.stringify({ events: batch });

        fetch("/api/events/", {
            method: "POST",
            headers: headers,
            body: body,
            keepalive: Boolean(useKeepalive),
        }).catch(function () {
            if (!isRetry) {
                setTimeout(function () {
                    sendBatch(batch, useKeepalive, true);
                }, 800);
            }
        });
    }

    function flush(options) {
        var useKeepalive = options && options.keepalive;
        while (queue.length > 0) {
            var batch = queue.splice(0, MAX_BATCH_SIZE);
            sendBatch(batch, useKeepalive, false);
        }
    }

    function track(eventType, payload, extra) {
        if (!eventType || typeof eventType !== "string") {
            return null;
        }
        var entrypoint = (extra && extra.entrypoint) || detectEntrypoint();
        if (!VALID_ENTRYPOINTS[entrypoint]) {
            entrypoint = "unknown";
        }
        var ev = {
            event_id: (extra && extra.event_id) || generateUuidV4(),
            event_type: eventType,
            ts: (extra && extra.ts) || new Date().toISOString(),
            session_id: sessionId,
            device: device,
            entrypoint: entrypoint,
            payload: payload && typeof payload === "object" ? payload : {},
        };
        if (extra && extra.geo && typeof extra.geo === "object") {
            ev.geo = extra.geo;
        }

        queue.push(ev);
        if (queue.length >= FLUSH_THRESHOLD) {
            flush({ keepalive: false });
        }
        return ev.event_id;
    }

    function emitDwellTimeAndFlush() {
        if (!dwellSent) {
            dwellSent = true;
            var now = Date.now();
            if (document.visibilityState !== "hidden") {
                visibleAccumulatedMs += Math.max(0, now - lastVisibleTimestamp);
                lastVisibleTimestamp = now;
            }
            var totalSeconds = Math.max(
                1,
                Math.round((visibleAccumulatedMs || now - pageLoadedAt) / 1000)
            );
            maxScrollPct = Math.max(maxScrollPct, computeScrollPct());
            track("dwell_time", {
                view: detectCurrentView(),
                seconds: totalSeconds,
                max_scroll_pct: maxScrollPct,
            });
        }
        flush({ keepalive: true });
    }

    window.addEventListener(
        "scroll",
        function () {
            var pct = computeScrollPct();
            if (pct > maxScrollPct) {
                maxScrollPct = pct;
            }
        },
        { passive: true }
    );

    document.addEventListener("visibilitychange", function () {
        var now = Date.now();
        if (document.visibilityState === "hidden") {
            visibleAccumulatedMs += Math.max(0, now - lastVisibleTimestamp);
            lastVisibleTimestamp = now;
            emitDwellTimeAndFlush();
        } else {
            lastVisibleTimestamp = now;
            dwellSent = false;
        }
    });

    window.addEventListener("pagehide", function () {
        emitDwellTimeAndFlush();
    });

    document.addEventListener("DOMContentLoaded", function () {
        maxScrollPct = computeScrollPct();
        var viewName = detectCurrentView();
        var payload = { view: viewName };
        if (document.referrer) {
            payload.referrer = document.referrer.slice(0, 500);
        }
        track("page_view", payload);

        if (!flushTimer) {
            flushTimer = setInterval(function () {
                if (queue.length > 0) {
                    flush({ keepalive: false });
                }
            }, FLUSH_INTERVAL_MS);
        }
    });

    window.Telemetry = {
        track: track,
        flush: flush,
        getSessionId: function () {
            return sessionId;
        },
        getDevice: function () {
            return device;
        },
        getEntrypoint: detectEntrypoint,
        getContextHeaders: getContextHeaders,
    };
})();
