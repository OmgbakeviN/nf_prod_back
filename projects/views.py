from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Count, Q

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Project, ProjectMember
from .permissions import IsProducer, CanAccessProject
from .serializers import (
    ProjectListSerializer,
    ProjectCreateUpdateSerializer,
    ProjectDetailSerializer,
    ProjectMemberSerializer,
    ProjectMemberCreateSerializer,
    ProjectMemberUpdateSerializer,
)

User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user

        queryset = (
            Project.objects
            .select_related("created_by")
            .prefetch_related("members", "members__user")
            .annotate(members_count=Count("members"))
        )

        if user.role == "PRODUCER":
            return queryset

        return queryset.filter(members__user=user).distinct()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProjectCreateUpdateSerializer
        if self.action == "retrieve":
            return ProjectDetailSerializer
        return ProjectListSerializer

    def get_permissions(self):
        if self.action in ["create", "destroy"]:
            return [IsAuthenticated(), IsProducer()]

        if self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsProducer()]

        return [IsAuthenticated()]

    def perform_create(self, serializer):
        project = serializer.save(created_by=self.request.user)

        ProjectMember.objects.create(
            project=project,
            user=self.request.user,
            role="PRODUCER",
        )

    @extend_schema(
        summary="List projects",
        description=(
            "Returns all projects for producers/admins. "
            "For normal users, returns only projects where the authenticated user is assigned."
        ),
        tags=["Projects"],
        responses={200: ProjectListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create project",
        description="Allows a producer/admin to create a new audiovisual production project.",
        tags=["Projects"],
        request=ProjectCreateUpdateSerializer,
        responses={201: ProjectDetailSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve project",
        description=(
            "Returns full project details. Producers can view all projects. "
            "Other users can only view projects where they are assigned."
        ),
        tags=["Projects"],
        responses={200: ProjectDetailSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        project = self.get_object()

        if request.user.role != "PRODUCER":
            self.check_object_permissions(request, project)

        serializer = ProjectDetailSerializer(project, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update project",
        description="Allows a producer/admin to update project information.",
        tags=["Projects"],
        request=ProjectCreateUpdateSerializer,
        responses={200: ProjectDetailSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete project",
        description="Allows a producer/admin to delete a project.",
        tags=["Projects"],
        responses={204: OpenApiResponse(description="Project deleted successfully.")},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ProjectMemberViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_project(self, request, project_pk):
        project = Project.objects.get(pk=project_pk)

        if request.user.role != "PRODUCER":
            if not ProjectMember.objects.filter(project=project, user=request.user).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You do not have access to this project.")

        return project

    @extend_schema(
        summary="List project members",
        description=(
            "Returns members assigned to a project. Producers can access all projects. "
            "Other users can only access members of projects where they are assigned."
        ),
        tags=["Project Members"],
        responses={200: ProjectMemberSerializer(many=True)},
    )
    def list(self, request, project_pk=None):
        project = self.get_project(request, project_pk)

        members = (
            ProjectMember.objects
            .filter(project=project)
            .select_related("user", "project")
            .order_by("-joined_at")
        )

        serializer = ProjectMemberSerializer(
            members,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data)

    @extend_schema(
        summary="Add project member",
        description=(
            "Allows a producer/admin to add a user to a project with a specific production role. "
            "The assigned user receives an email notification."
        ),
        tags=["Project Members"],
        request=ProjectMemberCreateSerializer,
        responses={201: ProjectMemberSerializer},
    )
    def create(self, request, project_pk=None):
        if request.user.role != "PRODUCER":
            return Response(
                {"detail": "Only producers/admins can add project members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        project = Project.objects.get(pk=project_pk)

        serializer = ProjectMemberCreateSerializer(
            data=request.data,
            context={"project": project},
        )
        serializer.is_valid(raise_exception=True)

        member = serializer.save(project=project)

        send_mail(
            subject=f"You have been added to project: {project.title}",
            message=(
                f"Hello {member.user.full_name},\n\n"
                f"You have been added to the project '{project.title}'.\n\n"
                f"Your project role: {member.role}\n"
                f"Character: {member.character_name or 'N/A'}\n\n"
                f"Please login to the platform to view the project details.\n\n"
                f"Production team."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member.user.email],
            fail_silently=False,
        )

        output = ProjectMemberSerializer(member, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Update project member",
        description=(
            "Allows a producer/admin to update a member role or character information inside a project. "
            "The user receives an email notification."
        ),
        tags=["Project Members"],
        request=ProjectMemberUpdateSerializer,
        responses={200: ProjectMemberSerializer},
    )
    def partial_update(self, request, project_pk=None, pk=None):
        if request.user.role != "PRODUCER":
            return Response(
                {"detail": "Only producers/admins can update project members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        project = Project.objects.get(pk=project_pk)
        member = ProjectMember.objects.get(project=project, pk=pk)

        serializer = ProjectMemberUpdateSerializer(member, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        member = serializer.save()

        send_mail(
            subject=f"Your project role has been updated: {project.title}",
            message=(
                f"Hello {member.user.full_name},\n\n"
                f"Your assignment in '{project.title}' has been updated.\n\n"
                f"Role: {member.role}\n"
                f"Character: {member.character_name or 'N/A'}\n\n"
                f"Production team."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member.user.email],
            fail_silently=False,
        )

        output = ProjectMemberSerializer(member, context={"request": request})
        return Response(output.data)

    @extend_schema(
        summary="Remove project member",
        description=(
            "Allows a producer/admin to remove a member from a project. "
            "The removed user receives an email notification."
        ),
        tags=["Project Members"],
        responses={204: OpenApiResponse(description="Project member removed successfully.")},
    )
    def destroy(self, request, project_pk=None, pk=None):
        if request.user.role != "PRODUCER":
            return Response(
                {"detail": "Only producers/admins can remove project members."},
                status=status.HTTP_403_FORBIDDEN,
            )

        project = Project.objects.get(pk=project_pk)
        member = ProjectMember.objects.get(project=project, pk=pk)

        user_email = member.user.email
        user_name = member.user.full_name
        project_title = project.title

        member.delete()

        send_mail(
            subject=f"You have been removed from project: {project_title}",
            message=(
                f"Hello {user_name},\n\n"
                f"You have been removed from the project '{project_title}'.\n\n"
                f"Production team."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)