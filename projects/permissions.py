from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import ProjectMember


class IsProducer(BasePermission):
    message = "Only producers/admins can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "PRODUCER"
        )


class CanAccessProject(BasePermission):
    message = "You do not have access to this project."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "PRODUCER":
            return True

        return ProjectMember.objects.filter(
            project=obj,
            user=request.user,
        ).exists()