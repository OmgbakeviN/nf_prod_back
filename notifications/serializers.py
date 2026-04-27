from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "type",
            "is_read",
            "related_project_id",
            "related_url",
            "created_at",
        ]