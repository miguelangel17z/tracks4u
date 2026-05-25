from django.urls import path
from .views import estado_page, estado_sistema

urlpatterns = [
    path("estado/", estado_page, name="estado-page"),
    path("estado/api/", estado_sistema, name="estado-api"),
]