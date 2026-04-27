from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Project, ProjectMember

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "phone", "role", "avatar_url"]

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class ProjectListSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    members_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "slug",
            "project_type",
            "genre",
            "short_description",
            "status",
            "cover_image",
            "cover_image_url",
            "members_count",
            "created_at",
            "updated_at",
        ]

    def get_cover_image_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "title",
            "project_type",
            "genre",
            "short_description",
            "synopsis",
            "status",
            "cover_image",
        ]


class ProjectMemberSerializer(serializers.ModelSerializer):
    user_details = SimpleUserSerializer(source="user", read_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            "id",
            "project",
            "user",
            "user_details",
            "role",
            "character_name",
            "character_description",
            "joined_at",
        ]
        read_only_fields = ["id", "project", "joined_at"]


class ProjectMemberCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = [
            "user",
            "role",
            "character_name",
            "character_description",
        ]

    def validate(self, attrs):
        project = self.context.get("project")
        user = attrs.get("user")

        if project and user and ProjectMember.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError("This user is already assigned to this project.")

        return attrs


class ProjectMemberUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMember
        fields = [
            "role",
            "character_name",
            "character_description",
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    created_by_details = SimpleUserSerializer(source="created_by", read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "slug",
            "project_type",
            "genre",
            "short_description",
            "synopsis",
            "status",
            "cover_image",
            "cover_image_url",
            "created_by",
            "created_by_details",
            "members",
            "created_at",
            "updated_at",
        ]

    def get_cover_image_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None