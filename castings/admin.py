from django.contrib import admin
from .models import Casting, Application
# Register your models here.

@admin.register(Casting)
class CastingAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "is_public", "deadline", "created_by", "created_at")
    list_filter = ("status", "is_public")
    search_fields = ("title", "description")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "casting", "preferred_role", "status", "created_at")
    list_filter = ("status", "preferred_role", "gender")
    search_fields = ("full_name", "email", "phone", "location")