from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiResponse

from projects.models import Project
from notifications.services import notify_project_team

from .models import ShootingLocation, ScheduleEvent
from .permissions import can_access_project, can_manage_planning
from .serializers import ShootingLocationSerializer, ScheduleEventSerializer


class BaseProjectNestedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        project_id = self.kwargs.get("project_pk")

        try:
            self.project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise NotFound("Project not found.")

        if not can_access_project(request.user, self.project):
            raise PermissionDenied("You do not have access to this project.")


class ShootingLocationViewSet(BaseProjectNestedViewSet):
    serializer_class = ShootingLocationSerializer

    def get_queryset(self):
        return ShootingLocation.objects.filter(project=self.project)

    @extend_schema(
        summary="List shooting locations",
        description="Returns all shooting locations for a project. Project members can view locations.",
        tags=["Locations"],
        responses={200: ShootingLocationSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create shooting location",
        description="Allows producers, directors or authorized crew members to create a shooting location. The project team receives notifications.",
        tags=["Locations"],
        request=ShootingLocationSerializer,
        responses={201: ShootingLocationSerializer},
    )
    def create(self, request, *args, **kwargs):
        if not can_manage_planning(request.user, self.project):
            raise PermissionDenied("You cannot create locations for this project.")

        serializer = ShootingLocationSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        location = serializer.save(project=self.project)

        notify_project_team(
            project=self.project,
            title=f"New shooting location: {self.project.title}",
            message=(
                f"A new shooting location has been added to project '{self.project.title}'.\n\n"
                f"Location: {location.name}\n"
                f"Address: {location.address}, {location.city}\n\n"
                f"Please login to view the details."
            ),
            notification_type="LOCATION",
            related_url=f"/projects/{self.project.id}/locations",
            exclude_user_ids=[request.user.id],
        )

        return Response(ShootingLocationSerializer(location, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Update shooting location",
        description="Allows producers, directors or authorized crew members to update a shooting location. The project team receives notifications.",
        tags=["Locations"],
        request=ShootingLocationSerializer,
        responses={200: ShootingLocationSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        if not can_manage_planning(request.user, self.project):
            raise PermissionDenied("You cannot update locations for this project.")

        location = self.get_object()
        serializer = ShootingLocationSerializer(location, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        location = serializer.save()

        notify_project_team(
            project=self.project,
            title=f"Shooting location updated: {self.project.title}",
            message=(
                f"A shooting location has been updated in project '{self.project.title}'.\n\n"
                f"Location: {location.name}\n"
                f"Address: {location.address}, {location.city}"
            ),
            notification_type="LOCATION",
            related_url=f"/projects/{self.project.id}/locations",
            exclude_user_ids=[request.user.id],
        )

        return Response(ShootingLocationSerializer(location, context={"request": request}).data)

    @extend_schema(
        summary="Delete shooting location",
        description="Allows producers, directors or authorized crew members to delete a shooting location.",
        tags=["Locations"],
        responses={204: OpenApiResponse(description="Location deleted successfully.")},
    )
    def destroy(self, request, *args, **kwargs):
        if not can_manage_planning(request.user, self.project):
            raise PermissionDenied("You cannot delete locations for this project.")

        location = self.get_object()
        name = location.name
        location.delete()

        notify_project_team(
            project=self.project,
            title=f"Shooting location deleted: {self.project.title}",
            message=f"The shooting location '{name}' has been deleted from project '{self.project.title}'.",
            notification_type="LOCATION",
            related_url=f"/projects/{self.project.id}/locations",
            exclude_user_ids=[request.user.id],
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class ScheduleEventViewSet(BaseProjectNestedViewSet):
    serializer_class = ScheduleEventSerializer

    def get_queryset(self):
        return (
            ScheduleEvent.objects
            .filter(project=self.project)
            .select_related("location", "created_by")
        )

    @extend_schema(
        summary="List schedule events",
        description="Returns schedule events for a project. Project members can view the planning.",
        tags=["Schedule"],
        responses={200: ScheduleEventSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create schedule event",
        description="Creates a production event such as shooting, rehearsal, meeting or deadline. The whole project team receives notifications.",
        tags=["Schedule"],
        request=ScheduleEventSerializer,
        responses={201: ScheduleEventSerializer},
    )
    def create(self, request, *args, **kwargs):
        if not can_manage_planning(request.user, self.project):
            raise PermissionDenied("You cannot create schedule events for this project.")

        serializer = ScheduleEventSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        event = serializer.save(project=self.project, created_by=request.user)

        notify_project_team(
            project=self.project,
            title=f"New schedule event: {self.project.title}",
            message=(
                f"A new event has been added to project '{self.project.title}'.\n\n"
                f"Event: {event.title}\n"
                f"Type: {event.event_type}\n"
                f"Start: {event.start_datetime}\n"
                f"End: {event.end_datetime}\n\n"
                f"Please login to view your planning."
            ),
            notification_type="SCHEDULE",
            related_url=f"/projects/{self.project.id}/schedule",
            exclude_user_ids=[request.user.id],
        )

        return Response(ScheduleEventSerializer(event, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Update schedule event",
        description="Updates a production event. The whole project team receives notifications.",
        tags=["Schedule"],
        request=ScheduleEventSerializer,
        responses={200: ScheduleEventSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        if not can_manage_planning(request.user, self.project):
            raise PermissionDenied("You cannot update schedule events for this project.")

        event = self.get_object()
        serializer = ScheduleEventSerializer(event, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        event = serializer.save()

        notify_project_team(
            project=self.project,
            title=f"Schedule updated: {self.project.title}",
            message=(
                f"The planning has been updated for project '{self.project.title}'.\n\n"
                f"Event: {event.title}\n"
                f"Type: {event.event_type}\n"
                f"Start: {event.start_datetime}\n"
                f"End: {event.end_datetime}"
            ),
            notification_type="SCHEDULE",
            related_url=f"/projects/{self.project.id}/schedule",
            exclude_user_ids=[request.user.id],
        )

        return Response(ScheduleEventSerializer(event, context={"request": request}).data)

    @extend_schema(
        summary="Delete schedule event",
        description="Deletes a schedule event. The whole project team receives notifications.",
        tags=["Schedule"],
        responses={204: OpenApiResponse(description="Schedule event deleted successfully.")},
    )
    def destroy(self, request, *args, **kwargs):
        if not can_manage_planning(request.user, self.project):
            raise PermissionDenied("You cannot delete schedule events for this project.")

        event = self.get_object()
        title = event.title
        event.delete()

        notify_project_team(
            project=self.project,
            title=f"Schedule event cancelled: {self.project.title}",
            message=f"The event '{title}' has been removed from project '{self.project.title}'.",
            notification_type="SCHEDULE",
            related_url=f"/projects/{self.project.id}/schedule",
            exclude_user_ids=[request.user.id],
        )

        return Response(status=status.HTTP_204_NO_CONTENT)