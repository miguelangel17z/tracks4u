from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .api.serializers import LoginSerializer,UserSerializer,UpdateProfileSerializer
from .service import AuthService, RegisterService, UpdateProfileService
from django.shortcuts import render
from .models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'home.html'

class loginView(TemplateView):
    template_name = 'loginTemplate.html'


class RegisterView(TemplateView):
    template_name = 'registerTemplate.html'

    
class UpdateProfileView(TemplateView):
    template_name = 'UpdateProfileTemplate.html'




    








