from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    PROJECT = "PROJECT", "Project"
    FILE = "FILE", "File"
    SCHEDULE = "SCHEDULE", "Schedule"
    LOCATION = "LOCATION", "Location"
    CASTING = "CASTING", "Casting"
    SYSTEM = "SYSTEM", "System"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )

    is_read = models.BooleanField(default=False)

    related_project_id = models.PositiveIntegerField(null=True, blank=True)
    related_url = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.title}"