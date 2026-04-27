from rest_framework import serializers
from .models import Casting, Application


class CastingListSerializer(serializers.ModelSerializer):
    applications_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Casting
        fields = [
            "id",
            "title",
            "description",
            "requirements",
            "deadline",
            "status",
            "is_public",
            "applications_count",
            "created_at",
            "updated_at",
        ]


class CastingCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Casting
        fields = [
            "title",
            "description",
            "requirements",
            "deadline",
            "status",
            "is_public",
        ]


class CastingDetailSerializer(serializers.ModelSerializer):
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Casting
        fields = [
            "id",
            "title",
            "description",
            "requirements",
            "deadline",
            "status",
            "is_public",
            "applications_count",
            "created_at",
            "updated_at",
        ]

    def get_applications_count(self, obj):
        return obj.applications.count()


class PublicCastingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Casting
        fields = [
            "id",
            "title",
            "description",
            "requirements",
            "deadline",
            "status",
        ]


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            "full_name",
            "age",
            "gender",
            "phone",
            "email",
            "location",
            "acting_experience",
            "experience_details",
            "portfolio_link",
            "languages",
            "special_skills",
            "camera_confidence",
            "available_for_filming",
            "available_for_rehearsals",
            "motivation",
            "reliability_reason",
            "preferred_role",
            "role_limitations",
            "headshot",
            "video",
            "commitment_confirmed",
            "signed_name",
        ]

    def validate_camera_confidence(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("Camera confidence must be between 1 and 10.")
        return value

    def validate_commitment_confirmed(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm your commitment.")
        return value


class ApplicationListSerializer(serializers.ModelSerializer):
    casting_title = serializers.CharField(source="casting.title", read_only=True)
    headshot_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "casting",
            "casting_title",
            "full_name",
            "age",
            "gender",
            "phone",
            "email",
            "location",
            "preferred_role",
            "status",
            "headshot_url",
            "video_url",
            "created_at",
        ]

    def get_headshot_url(self, obj):
        request = self.context.get("request")
        if obj.headshot and request:
            return request.build_absolute_uri(obj.headshot.url)
        return None

    def get_video_url(self, obj):
        request = self.context.get("request")
        if obj.video and request:
            return request.build_absolute_uri(obj.video.url)
        return None


class ApplicationDetailSerializer(serializers.ModelSerializer):
    casting_title = serializers.CharField(source="casting.title", read_only=True)
    headshot_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = "__all__"

    def get_headshot_url(self, obj):
        request = self.context.get("request")
        if obj.headshot and request:
            return request.build_absolute_uri(obj.headshot.url)
        return None

    def get_video_url(self, obj):
        request = self.context.get("request")
        if obj.video and request:
            return request.build_absolute_uri(obj.video.url)
        return None


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)