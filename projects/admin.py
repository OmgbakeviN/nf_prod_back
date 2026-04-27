from django.contrib import admin
from .models import Project, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "project_type", "status", "created_by", "created_at")
    list_filter = ("project_type", "status")
    search_fields = ("title", "short_description", "synopsis")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProjectMemberInline]


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "role", "character_name", "joined_at")
    list_filter = ("role",)
    search_fields = ("project__title", "user__email", "user__full_name", "character_name")