from rest_framework.permissions import BasePermission


class IsProducer(BasePermission):
    message = "Only producers/admins can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "PRODUCER"
        )


class IsOwnerOrProducer(BasePermission):
    message = "You can only access your own profile."

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.role == "PRODUCER"