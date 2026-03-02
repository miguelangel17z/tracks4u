from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class AuthService:
    @staticmethod
    def login(password: str, email: str = None, username: str = None) -> dict:
        if email:
            user = authenticate(email, password)
            
        elif username:
            user = authenticate(username=username, password=password)     
        
        if user is None:
            raise ValueError("Incorrect username or password")
        
        
        refresh = RefreshToken.for_user(user)

        return{
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

class RegisterService:
    def register(data:dict):
        User.objects.create_user( username=data["username"],
            email=data["email"],
            password=data["password"])
