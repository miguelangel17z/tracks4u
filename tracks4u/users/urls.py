from django.urls import include, path

from .views import loginView,RegisterView, UpdateProfileView, HomeView
from .api.views import loginView as apiLoginView, RegisterView as apiRegisterView, UpdateProfileView as apiUpdateProfileView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', loginView.as_view(), name='login'),
    path('api/login/', apiLoginView.as_view(), name='api-login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('api/register/', apiRegisterView.as_view(), name='api-register'),
    path('profile/', UpdateProfileView.as_view(), name='profile'),
    path('api/profile/', apiUpdateProfileView.as_view(), name='api-profile'),
    path('i18n/', include('django.conf.urls.i18n')),  # ← agregar
    


    
]
