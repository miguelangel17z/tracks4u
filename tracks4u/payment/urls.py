from django.urls import path

from .views import LicensingView

urlpatterns = [
    
    path('licensing/', LicensingView.as_view(),name="licensing"),
]
