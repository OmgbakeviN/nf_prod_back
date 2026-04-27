from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserRole(models.TextChoices):
    PRODUCER = "PRODUCER", "Producer"
    DIRECTOR = "DIRECTOR", "Director"
    SCRIPTWRITER = "SCRIPTWRITER", "Scriptwriter"
    ACTOR = "ACTOR", "Actor"
    CREW = "CREW", "Crew"


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email address is required.")

        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.PRODUCER)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=False, blank=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.ACTOR,
    )
    invited_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_users",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def is_producer(self):
        return self.role == UserRole.PRODUCER