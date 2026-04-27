from django.contrib import admin
from .models import ShootingLocation, ScheduleEvent


@admin.register(ShootingLocation)
class ShootingLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "city", "created_at")
    search_fields = ("name", "address", "city", "project__title")


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "event_type", "start_datetime", "end_datetime")
    list_filter = ("event_type",)
    search_fields = ("title", "project__title", "description")