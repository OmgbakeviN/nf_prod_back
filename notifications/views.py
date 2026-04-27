from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")

    @extend_schema(
        summary="List notifications",
        description="Returns notifications for the authenticated user.",
        tags=["Notifications"],
        responses={200: NotificationSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve notification",
        description="Returns details of a single notification belonging to the authenticated user.",
        tags=["Notifications"],
        responses={200: NotificationSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Mark notification as read",
        description="Marks one notification as read.",
        tags=["Notifications"],
        responses={200: NotificationSerializer},
    )
    @action(detail=True, methods=["patch"], url_path="read")
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()

        serializer = NotificationSerializer(notification)
        return Response(serializer.data)

    @extend_schema(
        summary="Mark all notifications as read",
        description="Marks all notifications of the authenticated user as read.",
        tags=["Notifications"],
        responses={200: OpenApiResponse(description="All notifications marked as read.")},
    )
    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        self.get_queryset().update(is_read=True)
        return Response({"detail": "All notifications marked as read."}, status=status.HTTP_200_OK)