from django.db import models
from django.conf import settings
# Create your models here.

class CastingStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class ApplicationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO", "Needs more info"


class PreferredRole(models.TextChoices):
    LEAD = "LEAD", "Lead"
    SUPPORTING = "SUPPORTING", "Supporting"
    EXTRA = "EXTRA", "Extra"


class Gender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"
    OTHER = "OTHER", "Other"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", "Prefer not to say"


class Casting(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=CastingStatus.choices,
        default=CastingStatus.OPEN,
    )
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="castings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Application(models.Model):
    casting = models.ForeignKey(
        Casting,
        on_delete=models.CASCADE,
        related_name="applications",
    )

    full_name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=30, choices=Gender.choices)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    location = models.CharField(max_length=255)

    acting_experience = models.BooleanField(default=False)
    experience_details = models.TextField(blank=True)
    portfolio_link = models.URLField(blank=True)

    languages = models.CharField(max_length=255)
    special_skills = models.TextField(blank=True)
    camera_confidence = models.PositiveSmallIntegerField()

    available_for_filming = models.BooleanField(default=False)
    available_for_rehearsals = models.BooleanField(default=False)

    motivation = models.TextField()
    reliability_reason = models.TextField()

    preferred_role = models.CharField(
        max_length=30,
        choices=PreferredRole.choices,
        default=PreferredRole.SUPPORTING,
    )
    role_limitations = models.TextField(blank=True)

    headshot = models.ImageField(upload_to="applications/headshots/")
    video = models.FileField(upload_to="applications/videos/")

    commitment_confirmed = models.BooleanField(default=False)
    signed_name = models.CharField(max_length=255)

    status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
    )

    admin_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_applications",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.casting.title}"