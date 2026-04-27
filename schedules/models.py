from django.conf import settings
from django.db import models


class ScheduleEventType(models.TextChoices):
    SHOOTING = "SHOOTING", "Shooting"
    REHEARSAL = "REHEARSAL", "Rehearsal"
    MEETING = "MEETING", "Meeting"
    DEADLINE = "DEADLINE", "Deadline"
    OTHER = "OTHER", "Other"


class ShootingLocation(models.Model):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="locations",
    )

    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    image = models.ImageField(upload_to="projects/locations/", blank=True, null=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.project.title}"


class ScheduleEvent(models.Model):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="schedule_events",
    )

    title = models.CharField(max_length=255)

    event_type = models.CharField(
        max_length=30,
        choices=ScheduleEventType.choices,
        default=ScheduleEventType.SHOOTING,
    )

    description = models.TextField(blank=True)

    location = models.ForeignKey(
        ShootingLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_schedule_events",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return f"{self.title} - {self.project.title}"