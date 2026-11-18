from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from tracks.models import Genre
from users.models import User


class UsersAndArtistOnboardingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="onboard_user",
            email="onboard@example.com",
            password="SafePassword123!",
            country="Colombia",
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.genre, _ = Genre.objects.get_or_create(name="Reggaeton")

    def test_profile_demographics_and_become_artist_flow(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        res_patch = self.client.patch(
            "/users/api/profile/",
            {
                "country": "Colombia",
                "birth_date": "2000-05-15",
                "gender": "MALE",
                "ethnicity": "Latino",
            },
            format="json",
        )
        self.assertEqual(res_patch.status_code, 200)

        # Invalid future birth_date rejected
        res_bad_birth = self.client.patch(
            "/users/api/profile/",
            {"birth_date": "2099-01-01"},
            format="json",
        )
        self.assertEqual(res_bad_birth.status_code, 400)

        # Non-artist cannot PATCH /users/api/artist/ -> 403
        res_not_artist = self.client.patch(
            "/users/api/artist/",
            {"bio": "Not an artist yet"},
            format="json",
        )
        self.assertEqual(res_not_artist.status_code, 403)

        # Become artist -> 201
        res_become = self.client.post(
            "/users/api/become-artist/",
            {
                "stage_name": "MC Medellin",
                "bio": "Urbano de Medellin",
                "country": "Colombia",
                "genre_ids": [self.genre.id],
            },
            format="json",
        )
        self.assertEqual(res_become.status_code, 201)
        artist_id = res_become.data["id"]

        # Duplicate become-artist rejected -> 400
        res_dup = self.client.post(
            "/users/api/become-artist/",
            {"stage_name": "MC Medellin 2"},
            format="json",
        )
        self.assertEqual(res_dup.status_code, 400)

        # Public artist profile -> 200
        self.client.credentials()
        res_public = self.client.get(f"/api/artists/{artist_id}/")
        self.assertEqual(res_public.status_code, 200)
        self.assertEqual(res_public.data["stage_name"], "MC Medellin")
