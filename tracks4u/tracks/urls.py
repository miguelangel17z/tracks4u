from django.urls import path

from .views import TrackCreateView, TrackListView

urlpatterns = [
    path('', TrackListView.as_view(), name='track-list'),
    path('crear/', TrackCreateView.as_view(), name='track-create'),
]
