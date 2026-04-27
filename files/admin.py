from django.contrib import admin
from .models import ProjectFile


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "project",
        "file_type",
        "status",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("file_type", "status")
    search_fields = ("title", "project__title", "uploaded_by__email")