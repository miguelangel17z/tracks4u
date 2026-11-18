from datetime import timedelta
import uuid

from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from telemetry.models import TelemetryEvent
from telemetry.schemas import validate_payload
from telemetry.services import emit_event
from telemetry.tasks import purge_acked_events
from users.models import User


@override_settings(
    TELEMETRY_DRAIN_TOKEN="test_drain_token_12345678901234567890",
    TELEMETRY_SETTLE_SECONDS=0,
    TELEMETRY_RETENTION_DAYS=7,
    TELEMETRY_DRAIN_MAX_LIMIT=1000,
)
class TelemetryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="telem_user",
            email="telem@example.com",
            password="SafePassword123!",
            country="Colombia",
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.drain_headers = {
            "HTTP_AUTHORIZATION": "Bearer test_drain_token_12345678901234567890"
        }

    def test_validate_payload_families(self):
        self.assertEqual(validate_payload("play_start", {"track_id": 10}), [])
        self.assertNotEqual(validate_payload("play_start", {"track_id": "uuid-str"}), [])
        self.assertEqual(
            validate_payload(
                "play_progress",
                {"track_id": 1, "position_sec": 15, "percent_listened": 50},
            ),
            [],
        )
        self.assertNotEqual(
            validate_payload(
                "play_progress",
                {"track_id": 1, "position_sec": 15, "percent_listened": 120},
            ),
            [],
        )
        self.assertEqual(
            validate_payload(
                "search",
                {
                    "search_id": str(uuid.uuid4()),
                    "query": "reggaeton",
                    "results_count": 5,
                    "clicked_track_id": 3,
                },
            ),
            [],
        )
        self.assertNotEqual(
            validate_payload(
                "search",
                {"search_id": "not-a-uuid", "query": "pop", "results_count": 1},
            ),
            [],
        )
        self.assertEqual(
            validate_payload(
                "purchase_intent",
                {"track_id": 2, "stage": "completed", "order_id": 9, "price": 4.99},
            ),
            [],
        )
        self.assertNotEqual(
            validate_payload("purchase_intent", {"track_id": 2, "stage": "invalid"}),
            [],
        )

    def test_emit_event_inside_rolled_back_atomic_leaves_no_row(self):
        ev_id = uuid.uuid4()
        try:
            with transaction.atomic():
                emit_event(
                    "playlist_add",
                    user=self.user,
                    session_id="s_atomic",
                    payload={"playlist_id": 1, "track_id": 2, "position": 1},
                    event_id=ev_id,
                )
                raise RuntimeError("Force rollback")
        except RuntimeError:
            pass

        self.assertFalse(TelemetryEvent.objects.filter(event_id=ev_id).exists())

    def test_ingest_endpoint_accepts_deduplicates_rejects_and_ignores_body_user_id(self):
        ev1_id = str(uuid.uuid4())
        ev2_id = str(uuid.uuid4())
        future_ts = (timezone.now() + timedelta(minutes=15)).isoformat()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        res = self.client.post(
            "/api/events/",
            {
                "events": [
                    {
                        "event_id": ev1_id,
                        "event_type": "page_view",
                        "session_id": "s_front1",
                        "user_id": 999999,
                        "payload": {"view": "home"},
                    },
                    {
                        "event_id": ev1_id,
                        "event_type": "page_view",
                        "session_id": "s_front1",
                        "payload": {"view": "home"},
                    },
                    {
                        "event_id": ev2_id,
                        "event_type": "play_start",
                        "session_id": "s_front1",
                        "payload": {},
                    },
                    {
                        "event_id": str(uuid.uuid4()),
                        "event_type": "page_view",
                        "session_id": "s_front1",
                        "ts": future_ts,
                        "payload": {"view": "home"},
                    },
                ]
            },
            format="json",
        )
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.data["accepted"], 1)
        self.assertEqual(res.data["duplicates"], 1)
        self.assertEqual(len(res.data["rejected"]), 2)

        stored = TelemetryEvent.objects.get(event_id=ev1_id)
        self.assertEqual(stored.user_id, self.user.id)
        self.assertEqual(stored.geo, {"country": "Colombia"})

    def test_ingest_rejects_invalid_jwt_and_batch_over_100(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid.jwt.token")
        res = self.client.post(
            "/api/events/",
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "page_view",
                "session_id": "s_bad",
                "payload": {"view": "home"},
            },
            format="json",
        )
        self.assertEqual(res.status_code, 401)

        self.client.credentials()
        res_large = self.client.post(
            "/api/events/",
            {"events": [{"event_id": str(uuid.uuid4())} for _ in range(101)]},
            format="json",
        )
        self.assertEqual(res_large.status_code, 400)

    def test_drain_auth_settle_window_and_ack(self):
        res_no_token = self.client.get("/api/events/drain/")
        self.assertEqual(res_no_token.status_code, 401)

        res_bad_token = self.client.get(
            "/api/events/drain/",
            HTTP_AUTHORIZATION="Bearer wrong_token",
        )
        self.assertEqual(res_bad_token.status_code, 401)

        with override_settings(TELEMETRY_DRAIN_TOKEN=""):
            res_empty_cfg = self.client.get(
                "/api/events/drain/",
                **self.drain_headers,
            )
            self.assertEqual(res_empty_cfg.status_code, 401)

        ev1 = emit_event(
            "like",
            user=self.user,
            session_id="s_drain",
            payload={"track_id": 1},
        )
        ev2 = emit_event(
            "like",
            user=self.user,
            session_id="s_drain",
            payload={"track_id": 2},
        )

        # Ventana de asentamiento: un evento recién creado no aparece si TELEMETRY_SETTLE_SECONDS=60
        with override_settings(TELEMETRY_SETTLE_SECONDS=60):
            res_settled = self.client.get("/api/events/drain/", **self.drain_headers)
            self.assertEqual(res_settled.status_code, 200)
            self.assertEqual(len(res_settled.data["events"]), 0)

        # Con TELEMETRY_SETTLE_SECONDS=0 sí aparecen en orden
        res_page1 = self.client.get(
            "/api/events/drain/?since=0&limit=1",
            **self.drain_headers,
        )
        self.assertEqual(res_page1.status_code, 200)
        self.assertEqual(len(res_page1.data["events"]), 1)
        self.assertTrue(res_page1.data["has_more"])
        self.assertEqual(res_page1.data["next_cursor"], ev1.id)

        # Ack del primer evento
        res_ack = self.client.post(
            "/api/events/ack/",
            {"last_id": ev1.id},
            format="json",
            **self.drain_headers,
        )
        self.assertEqual(res_ack.status_code, 200)
        self.assertEqual(res_ack.data["acked"], 1)

        # Re-ejecutar ack es idempotente
        res_ack_again = self.client.post(
            "/api/events/ack/",
            {"last_id": ev1.id},
            format="json",
            **self.drain_headers,
        )
        self.assertEqual(res_ack_again.data["acked"], 0)

        # El siguiente drain desde since=0 solo devuelve ev2
        res_remaining = self.client.get(
            "/api/events/drain/?since=0&limit=10",
            **self.drain_headers,
        )
        self.assertEqual(len(res_remaining.data["events"]), 1)
        self.assertEqual(res_remaining.data["events"][0]["id"], ev2.id)

    def test_purge_acked_events_only_deletes_old_acked(self):
        old_acked = emit_event(
            "page_view",
            session_id="s_purge",
            payload={"view": "home"},
        )
        recent_acked = emit_event(
            "page_view",
            session_id="s_purge",
            payload={"view": "home"},
        )
        unacked = emit_event(
            "page_view",
            session_id="s_purge",
            payload={"view": "home"},
        )

        TelemetryEvent.objects.filter(id=old_acked.id).update(
            acked_at=timezone.now() - timedelta(days=10)
        )
        TelemetryEvent.objects.filter(id=recent_acked.id).update(
            acked_at=timezone.now() - timedelta(days=1)
        )

        deleted = purge_acked_events()
        self.assertEqual(deleted, 1)
        self.assertFalse(TelemetryEvent.objects.filter(id=old_acked.id).exists())
        self.assertTrue(TelemetryEvent.objects.filter(id=recent_acked.id).exists())
        self.assertTrue(TelemetryEvent.objects.filter(id=unacked.id).exists())
