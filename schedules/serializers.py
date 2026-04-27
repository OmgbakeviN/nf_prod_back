from rest_framework import serializers
from .models import ShootingLocation, ScheduleEvent


class ShootingLocationSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ShootingLocation
        fields = [
            "id",
            "project",
            "name",
            "address",
            "city",
            "description",
            "image",
            "image_url",
            "latitude",
            "longitude",
            "created_at",
        ]
        read_only_fields = ["id", "project", "created_at", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class ScheduleEventSerializer(serializers.ModelSerializer):
    location_details = ShootingLocationSerializer(source="location", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = ScheduleEvent
        fields = [
            "id",
            "project",
            "title",
            "event_type",
            "description",
            "location",
            "location_details",
            "start_datetime",
            "end_datetime",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "project", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_datetime", getattr(self.instance, "start_datetime", None))
        end = attrs.get("end_datetime", getattr(self.instance, "end_datetime", None))

        if start and end and end < start:
            raise serializers.ValidationError("End datetime must be after start datetime.")

        return attrs