from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "avatar",
            "avatar_url",
            "role",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "avatar_url"]

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class MeSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "avatar_url",
            "role",
            "is_staff",
            "is_superuser",
        ]

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class InviteUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=User._meta.get_field("role").choices)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        temporary_password = get_random_string(10)

        user = User.objects.create_user(
            email=validated_data["email"],
            password=temporary_password,
            full_name=validated_data["full_name"],
            phone=validated_data.get("phone", ""),
            role=validated_data["role"],
            invited_by=request.user if request else None,
            is_active=True,
        )

        user.temporary_password = temporary_password
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "phone", "role", "is_active", "avatar"]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "full_name",
            "phone",
            "avatar",
            "avatar_url",
        ]
        read_only_fields = ["avatar_url"]

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")

        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        validate_password(attrs["new_password"], self.context["request"].user)

        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user