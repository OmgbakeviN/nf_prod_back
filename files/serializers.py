from rest_framework import serializers
from .models import ProjectFile


class ProjectFileListSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)
    uploaded_by_role = serializers.CharField(source="uploaded_by.role", read_only=True)

    class Meta:
        model = ProjectFile
        fields = [
            "id",
            "project",
            "title",
            "description",
            "file",
            "file_url",
            "file_type",
            "version",
            "status",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_by_role",
            "created_at",
            "updated_at",
            "submitted_at",
            "reviewed_at",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class ProjectFileDetailSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)
    uploaded_by_email = serializers.CharField(source="uploaded_by.email", read_only=True)
    uploaded_by_role = serializers.CharField(source="uploaded_by.role", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.full_name", read_only=True)

    class Meta:
        model = ProjectFile
        fields = "__all__"

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class ProjectFileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = [
            "title",
            "description",
            "file",
            "file_type",
            "version",
            "status",
        ]

    def validate_status(self, value):
        request = self.context.get("request")

        if request and request.user.role != "PRODUCER" and value == "APPROVED":
            raise serializers.ValidationError("Only producers can upload directly as approved.")

        return value


class ProjectFileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = [
            "title",
            "description",
            "file",
            "file_type",
            "version",
            "status",
        ]

    def validate_status(self, value):
        request = self.context.get("request")

        if request and request.user.role != "PRODUCER" and value == "APPROVED":
            raise serializers.ValidationError("Only producers can approve files.")

        return value


class ProjectFileRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)


class ProjectFileActionSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)