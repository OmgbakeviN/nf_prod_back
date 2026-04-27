from django.conf import settings
from django.db import models


class ProjectFileType(models.TextChoices):
    SCRIPT = "SCRIPT", "Script"
    IMAGE = "IMAGE", "Image"
    CONTRACT = "CONTRACT", "Contract"
    STORYBOARD = "STORYBOARD", "Storyboard"
    PRODUCTION_NOTE = "PRODUCTION_NOTE", "Production note"
    OTHER = "OTHER", "Other"


class ProjectFileStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PENDING_REVIEW = "PENDING_REVIEW", "Pending review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class ProjectFile(models.Model):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="files",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_project_files",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    file = models.FileField(upload_to="projects/files/")
    file_type = models.CharField(
        max_length=30,
        choices=ProjectFileType.choices,
        default=ProjectFileType.OTHER,
    )

    version = models.CharField(max_length=50, blank=True, default="v1")

    status = models.CharField(
        max_length=30,
        choices=ProjectFileStatus.choices,
        default=ProjectFileStatus.DRAFT,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_project_files",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.project.title}"