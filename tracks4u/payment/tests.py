from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from payment.domain.builders import OrderBuilder
from payment.models import Order, OrderItem
from payment.services import OrderService
from tracks.models import Artist, Track
from users.models import User


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, NOTIFICATION_MODE="MOCK")
class OrderBuilderAndServiceTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username="buyer1",
            email="buyer1@example.com",
            password="SafePassword123!",
        )
        self.other_buyer = User.objects.create_user(
            username="buyer2",
            email="buyer2@example.com",
            password="SafePassword123!",
        )
        self.artist_user = User.objects.create_user(
            username="artist_user",
            email="artist@example.com",
            password="SafePassword123!",
        )
        self.artist = Artist.objects.create(
            user=self.artist_user,
            stage_name="Producer X",
        )
        self.track1 = Track.objects.create(
            artist=self.artist,
            title="Beat Alpha",
            price=Decimal("9.99"),
        )
        self.track2 = Track.objects.create(
            artist=self.artist,
            title="Beat Beta",
            price=Decimal("14.50"),
        )

    def test_builder_accumulates_errors(self):
        builder = OrderBuilder()
        builder.validar()
        self.assertGreaterEqual(len(builder.errores), 3)
        with self.assertRaises(ValueError):
            builder.construir()

    def test_builder_rejects_duplicate_tracks_in_same_order(self):
        builder = (
            OrderBuilder()
            .para_user(self.buyer)
            .agregar_track(self.track1)
            .agregar_track(self.track1)
            .con_pago("CARD")
        )
        with self.assertRaises(ValueError) as ctx:
            builder.construir()
        self.assertIn("Duplicate track", str(ctx.exception))

    def test_builder_rejects_artist_buying_own_track(self):
        builder = (
            OrderBuilder()
            .para_user(self.artist_user)
            .agregar_track(self.track1)
            .con_pago("CARD")
        )
        with self.assertRaises(ValueError) as ctx:
            builder.construir()
        self.assertIn("own track", str(ctx.exception))

    def test_service_creates_order_and_items_with_server_price_and_rejects_rebuy(self):
        with self.captureOnCommitCallbacks(execute=True):
            order = OrderService.crear_orden(
                user=self.buyer,
                track_ids=[self.track1.id, self.track2.id],
                payment_method="CARD",
            )

        self.assertEqual(order.status, "COMPLETED")
        self.assertEqual(order.total_amount, Decimal("24.49"))
        items = list(OrderItem.objects.filter(order=order).order_by("track_id"))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].price_paid, Decimal("9.99"))
        self.assertEqual(items[1].price_paid, Decimal("14.50"))

        with self.assertRaises(ValueError) as ctx:
            OrderService.crear_orden(
                user=self.buyer,
                track_ids=[self.track1.id],
                payment_method="PAYPAL",
            )
        self.assertIn("already own", str(ctx.exception))

    def test_service_rolls_back_when_track_does_not_exist(self):
        initial_count = Order.objects.count()
        with self.assertRaises(ValueError):
            OrderService.crear_orden(
                user=self.buyer,
                track_ids=[self.track1.id, 9999999],
                payment_method="CARD",
            )
        self.assertEqual(Order.objects.count(), initial_count)

    @mock.patch("tracks.infra.notifications.tasks.send_email_task.delay")
    def test_on_commit_enqueues_notification(self, mock_delay):
        with self.captureOnCommitCallbacks(execute=True):
            OrderService.crear_orden(
                user=self.buyer,
                track_ids=[self.track1.id],
                payment_method="PSE",
            )
        self.assertTrue(mock_delay.called)


class PaymentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.buyer = User.objects.create_user(
            username="api_buyer",
            email="api_buyer@example.com",
            password="SafePassword123!",
        )
        self.other = User.objects.create_user(
            username="api_other",
            email="api_other@example.com",
            password="SafePassword123!",
        )
        self.artist = Artist.objects.create(stage_name="API Artist")
        self.track = Track.objects.create(
            artist=self.artist,
            title="API Track",
            price=Decimal("5.00"),
        )
        self.token = str(RefreshToken.for_user(self.buyer).access_token)

    def test_orders_requires_jwt(self):
        res = self.client.post(
            "/payment/orders/",
            {"track_ids": [self.track.id], "payment_method": "CARD"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    def test_create_order_and_list_my_purchases_isolation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        res = self.client.post(
            "/payment/orders/",
            {"track_ids": [self.track.id], "payment_method": "CARD"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        order_id = res.data["id"]

        res_dup = self.client.post(
            "/payment/orders/",
            {"track_ids": [self.track.id], "payment_method": "CARD"},
            format="json",
        )
        self.assertEqual(res_dup.status_code, 400)

        res_purchases = self.client.get("/payment/my-purchases/")
        self.assertEqual(res_purchases.status_code, 200)
        self.assertEqual(res_purchases.data["count"], 1)

        other_token = str(RefreshToken.for_user(self.other).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_token}")
        res_other_purchases = self.client.get("/payment/my-purchases/")
        self.assertEqual(res_other_purchases.data["count"], 0)

        res_other_detail = self.client.get(f"/payment/orders/{order_id}/")
        self.assertEqual(res_other_detail.status_code, 404)
