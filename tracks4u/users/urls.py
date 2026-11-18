from django.urls import path

from .api.views import (
    ArtistProfileUpdateView,
    BecomeArtistView,
    RegisterView as apiRegisterView,
    UpdateProfileView as apiUpdateProfileView,
    loginView as apiLoginView,
)
from .views import HomeView, RegisterView, UpdateProfileView, loginView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", loginView.as_view(), name="login"),
    path("api/login/", apiLoginView.as_view(), name="api-login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("api/register/", apiRegisterView.as_view(), name="api-register"),
    path("profile/", UpdateProfileView.as_view(), name="profile"),
    path("api/profile/", apiUpdateProfileView.as_view(), name="api-profile"),
    path("api/become-artist/", BecomeArtistView.as_view(), name="api-become-artist"),
    path("api/artist/", ArtistProfileUpdateView.as_view(), name="api-artist-update"),
]
