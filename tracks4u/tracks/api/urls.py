from django.urls import path
from .api_views import TrackCreateAPIView, TrackListAPIView

urlpatterns = [
    path('', TrackListAPIView.as_view(), name='api-track-list'),
    path('crear/', TrackCreateAPIView.as_view(), name='api-track-create'),
]