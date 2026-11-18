from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Gestor para el modelo User mapeado a la tabla 'user' de PostgreSQL."""

    def create_user(self, username: str, email: str, password: str = None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        extra_fields.setdefault("app_role", "user")
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username: str, email: str, password: str = None, **extra_fields):
        extra_fields["app_role"] = "sysadmin"
        return self.create_user(username=username, email=email, password=password, **extra_fields)


class User(AbstractBaseUser):
    GENDER_CHOICES = [
        ("FEMALE", "Female"),
        ("MALE", "Male"),
        ("NON_BINARY", "Non-binary"),
        ("PREFER_NOT_TO_SAY", "Prefer not to say"),
    ]
    APP_ROLE_CHOICES = [
        ("user", "User"),
        ("sysadmin", "Sysadmin"),
    ]

    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.TextField()
    country = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True, choices=GENDER_CHOICES)
    ethnicity = models.CharField(max_length=100, null=True, blank=True)
    app_role = models.CharField(max_length=20, default="user", choices=APP_ROLE_CHOICES)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        managed = False
        db_table = "user"

    def __str__(self):
        return self.username

    @property
    def is_active(self) -> bool:
        return True

    @property
    def is_staff(self) -> bool:
        return self.app_role == "sysadmin"

    @property
    def is_superuser(self) -> bool:
        return self.app_role == "sysadmin"

    def has_perm(self, perm, obj=None) -> bool:
        return self.is_superuser

    def has_module_perms(self, app_label) -> bool:
        return self.is_superuser
