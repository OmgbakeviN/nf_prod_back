from django.conf import settings
from django.db import models
from django.utils.text import slugify


class ProjectType(models.TextChoices):
    FILM = "FILM", "Film"
    SERIES = "SERIES", "Series"
    YOUTUBE = "YOUTUBE", "YouTube"
    CLIP = "CLIP", "Music Clip"
    SHORT_FILM = "SHORT_FILM", "Short Film"
    OTHER = "OTHER", "Other"


class ProjectStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    CASTING = "CASTING", "Casting"
    PRE_PRODUCTION = "PRE_PRODUCTION", "Pre-production"
    PRODUCTION = "PRODUCTION", "Production"
    POST_PRODUCTION = "POST_PRODUCTION", "Post-production"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class ProjectRole(models.TextChoices):
    PRODUCER = "PRODUCER", "Producer"
    DIRECTOR = "DIRECTOR", "Director"
    SCRIPTWRITER = "SCRIPTWRITER", "Scriptwriter"
    ACTOR = "ACTOR", "Actor"
    CAMERAMAN = "CAMERAMAN", "Cameraman"
    EDITOR = "EDITOR", "Editor"
    CREW = "CREW", "Crew"


class Project(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)

    project_type = models.CharField(
        max_length=30,
        choices=ProjectType.choices,
        default=ProjectType.YOUTUBE,
    )
    genre = models.CharField(max_length=100, blank=True)

    short_description = models.TextField()
    synopsis = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=ProjectStatus.choices,
        default=ProjectStatus.DRAFT,
    )

    cover_image = models.ImageField(upload_to="projects/covers/", blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_projects",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProjectMember(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships",
    )

    role = models.CharField(
        max_length=30,
        choices=ProjectRole.choices,
        default=ProjectRole.ACTOR,
    )

    character_name = models.CharField(max_length=255, blank=True)
    character_description = models.TextField(blank=True)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.user.email} - {self.project.title} - {self.role}"