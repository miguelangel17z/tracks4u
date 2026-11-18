from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from playlists.models import Playlist, PlaylistTrack
from playlists.services import PlaylistService
from telemetry.models import TelemetryEvent
from tracks.models import Artist, Track
from users.models import User


class PlaylistServiceAndAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username="pl_owner_t7",
            email="pl_owner_t7@example.com",
            password="SafePassword123!",
        )
        self.other = User.objects.create_user(
            username="pl_other_t7",
            email="pl_other_t7@example.com",
            password="SafePassword123!",
        )
        self.owner_token = str(RefreshToken.for_user(self.owner).access_token)
        self.other_token = str(RefreshToken.for_user(self.other).access_token)

        self.artist = Artist.objects.create(stage_name="PL Test Artist")
        self.t1 = Track.objects.create(artist=self.artist, title="Song 1", price=Decimal("1.99"))
        self.t2 = Track.objects.create(artist=self.artist, title="Song 2", price=Decimal("2.99"))
        self.t3 = Track.objects.create(artist=self.artist, title="Song 3", price=Decimal("3.99"))

    def test_private_playlist_returns_404_for_other_users_and_public_is_visible(self):
        private_pl = PlaylistService.crear_playlist(
            owner=self.owner,
            name="Secret Mix",
            tags=["focus"],
            is_public=False,
        )
        public_pl = PlaylistService.crear_playlist(
            owner=self.owner,
            name="Public Mix",
            is_public=True,
        )

        # Anonymous cannot see private playlist -> 404
        res_anon_priv = self.client.get(f"/api/playlists/{private_pl.id}/")
        self.assertEqual(res_anon_priv.status_code, 404)

        # Other user cannot see private playlist -> 404
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.other_token}")
        res_other_priv = self.client.get(f"/api/playlists/{private_pl.id}/")
        self.assertEqual(res_other_priv.status_code, 404)

        # Anonymous can see public playlist -> 200
        self.client.credentials()
        res_anon_pub = self.client.get(f"/api/playlists/{public_pl.id}/")
        self.assertEqual(res_anon_pub.status_code, 200)

    def test_add_remove_reorder_and_playlist_add_telemetry(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.owner_token}")
        res_create = self.client.post(
            "/api/playlists/",
            {"name": "Workout Hits", "tags": ["gym", "energy"], "is_public": True},
            format="json",
        )
        self.assertEqual(res_create.status_code, 201)
        pl_id = res_create.data["id"]

        for track in (self.t1, self.t2, self.t3):
            res_add = self.client.post(
                f"/api/playlists/{pl_id}/tracks/",
                {"track_id": track.id},
                format="json",
                HTTP_X_SESSION_ID="s_playlist_test",
            )
            self.assertEqual(res_add.status_code, 201)

        # Duplicate add returns 400 and does not emit extra playlist_add event
        events_before = TelemetryEvent.objects.filter(
            event_type="playlist_add",
            session_id="s_playlist_test",
        ).count()
        self.assertEqual(events_before, 3)

        res_dup = self.client.post(
            f"/api/playlists/{pl_id}/tracks/",
            {"track_id": self.t1.id},
            format="json",
            HTTP_X_SESSION_ID="s_playlist_test",
        )
        self.assertEqual(res_dup.status_code, 400)
        self.assertEqual(
            TelemetryEvent.objects.filter(
                event_type="playlist_add",
                session_id="s_playlist_test",
            ).count(),
            3,
        )

        # Reorder tracks [t3, t1, t2]
        res_reorder = self.client.put(
            f"/api/playlists/{pl_id}/order/",
            {"track_ids": [self.t3.id, self.t1.id, self.t2.id]},
            format="json",
        )
        self.assertEqual(res_reorder.status_code, 200)
        positions = list(
            PlaylistTrack.objects.filter(playlist_id=pl_id)
            .order_by("position")
            .values_list("track_id", "position")
        )
        self.assertEqual(
            positions,
            [(self.t3.id, 1), (self.t1.id, 2), (self.t2.id, 3)],
        )

        # Remove middle track (t1) -> recompacts positions to 1..2
        res_del = self.client.delete(f"/api/playlists/{pl_id}/tracks/{self.t1.id}/")
        self.assertEqual(res_del.status_code, 204)
        positions_after = list(
            PlaylistTrack.objects.filter(playlist_id=pl_id)
            .order_by("position")
            .values_list("track_id", "position")
        )
        self.assertEqual(positions_after, [(self.t3.id, 1), (self.t2.id, 2)])
