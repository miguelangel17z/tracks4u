from django.urls import path

from .api.views import LicensingView as api_LicensingView


urlpatterns = [
    path('licensing/', api_LicensingView.as_view(), name='licensing'),
    
]
