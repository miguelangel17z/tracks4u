from decimal import Decimal

from django.test import TestCase

from charts.services import get_revenue, get_summary
from payment.services import OrderService
from tracks.models import Artist, Genre, Track, TrackGenre
from users.models import User


class ChartsServiceTests(TestCase):
    def test_revenue_by_genre_sums_to_total_revenue(self):
        buyer = User.objects.create_user(
            username="chart_buyer",
            email="chart_buyer@example.com",
            password="SafePassword123!",
        )
        artist = Artist.objects.create(stage_name="Chart Artist")
        g1, _ = Genre.objects.get_or_create(name="Pop")
        g2, _ = Genre.objects.get_or_create(name="Rock")

        t1 = Track.objects.create(artist=artist, title="Track Multi Genre", price=Decimal("10.00"))
        TrackGenre.objects.create(track=t1, genre=g1)
        TrackGenre.objects.create(track=t1, genre=g2)

        t2 = Track.objects.create(artist=artist, title="Track Single Genre", price=Decimal("5.50"))
        TrackGenre.objects.create(track=t2, genre=g1)

        OrderService.crear_orden(user=buyer, track_ids=[t1.id], payment_method="CARD")
        OrderService.crear_orden(user=buyer, track_ids=[t2.id], payment_method="PAYPAL")

        rev = get_revenue("30d")
        self.assertEqual(rev["total_revenue_usd"], 15.50)
        self.assertAlmostEqual(sum(rev["values"]), rev["total_revenue_usd"], places=2)

        summary = get_summary("30d")
        self.assertEqual(summary["total_sales"], 2)
        self.assertEqual(summary["total_revenue_usd"], 15.50)
        self.assertEqual(summary["avg_ticket_usd"], 7.75)
