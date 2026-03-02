from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # En producción, usar un sistema de hashing seguro
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username