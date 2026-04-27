from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsProducer(BasePermission):
    message = "Only producers/admins can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "PRODUCER"
        )


class IsProducerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "PRODUCER"
        )