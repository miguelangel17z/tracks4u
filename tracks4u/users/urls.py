from django.urls import path

from .views import loginView,RegisterView, UpdateProfileView, HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='Home'),
    path('login/', loginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UpdateProfileView.as_view(), name='Profile'),


    
]
