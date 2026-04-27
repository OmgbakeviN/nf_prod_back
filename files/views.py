from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiResponse

from projects.models import Project, ProjectMember
from .models import ProjectFile, ProjectFileStatus
from .permissions import (
    can_edit_file,
    can_submit_file,
    can_upload_file,
    can_view_file,
)
from .serializers import (
    ProjectFileActionSerializer,
    ProjectFileCreateSerializer,
    ProjectFileDetailSerializer,
    ProjectFileListSerializer,
    ProjectFileRejectSerializer,
    ProjectFileUpdateSerializer,
)


def get_project_team_emails(project):
    members = (
        ProjectMember.objects
        .filter(project=project)
        .select_related("user")
    )

    emails = []

    for member in members:
        if member.user.email:
            emails.append(member.user.email)

    return list(set(emails))


def notify_project_team(project, subject, message, exclude_emails=None):
    exclude_emails = exclude_emails or []
    emails = get_project_team_emails(project)
    emails = [email for email in emails if email not in exclude_emails]

    if emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            fail_silently=False,
        )


def notify_project_producers(project, subject, message):
    producer_emails = []

    if project.created_by.email:
        producer_emails.append(project.created_by.email)

    producer_members = (
        ProjectMember.objects
        .filter(project=project, role="PRODUCER")
        .select_related("user")
    )

    for member in producer_members:
        if member.user.email:
            producer_emails.append(member.user.email)

    producer_emails = list(set(producer_emails))

    if producer_emails:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=producer_emails,
            fail_silently=False,
        )


class ProjectFileViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        project_id = self.kwargs.get("project_pk")

        try:
            self.project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise NotFound("Project not found.")

        if request.user.role != "PRODUCER":
            exists = ProjectMember.objects.filter(
                project=self.project,
                user=request.user,
            ).exists()

            if not exists:
                raise PermissionDenied("You do not have access to this project.")

    def get_queryset(self):
        queryset = (
            ProjectFile.objects
            .filter(project=self.project)
            .select_related("project", "uploaded_by", "reviewed_by")
        )

        user = self.request.user

        if user.role == "PRODUCER":
            return queryset

        visible_ids = []

        for item in queryset:
            if can_view_file(user, item):
                visible_ids.append(item.id)

        return queryset.filter(id__in=visible_ids)

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectFileCreateSerializer

        if self.action in ["update", "partial_update"]:
            return ProjectFileUpdateSerializer

        if self.action == "retrieve":
            return ProjectFileDetailSerializer

        return ProjectFileListSerializer

    @extend_schema(
        summary="List project files",
        description=(
            "Returns files for a project. Producers see all files. "
            "Actors see only approved files. Scriptwriters/directors see approved files and their own drafts."
        ),
        tags=["Project Files"],
        responses={200: ProjectFileListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Upload project file",
        description=(
            "Allows producers, scriptwriters, directors or authorized crew members to upload a project file. "
            "Producer uploads can be approved directly. Other uploads are drafts or pending review."
        ),
        tags=["Project Files"],
        request=ProjectFileCreateSerializer,
        responses={201: ProjectFileDetailSerializer},
    )
    def create(self, request, *args, **kwargs):
        if not can_upload_file(request.user, self.project):
            return Response(
                {"detail": "You are not allowed to upload files to this project."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ProjectFileCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        chosen_status = serializer.validated_data.get("status", ProjectFileStatus.DRAFT)

        if request.user.role == "PRODUCER":
            status_value = chosen_status
        else:
            status_value = chosen_status
            if status_value == ProjectFileStatus.APPROVED:
                status_value = ProjectFileStatus.DRAFT

        project_file = serializer.save(
            project=self.project,
            uploaded_by=request.user,
            status=status_value,
        )

        notify_project_producers(
            self.project,
            subject=f"New file uploaded: {self.project.title}",
            message=(
                f"A new file has been uploaded in project '{self.project.title}'.\n\n"
                f"Title: {project_file.title}\n"
                f"Type: {project_file.file_type}\n"
                f"Uploaded by: {request.user.full_name}\n"
                f"Status: {project_file.status}\n\n"
                f"Please login to review it."
            ),
        )

        if project_file.status == ProjectFileStatus.APPROVED:
            notify_project_team(
                self.project,
                subject=f"New approved file available: {self.project.title}",
                message=(
                    f"A new approved file is available in project '{self.project.title}'.\n\n"
                    f"Title: {project_file.title}\n"
                    f"Type: {project_file.file_type}\n"
                    f"Version: {project_file.version}\n\n"
                    f"Please login to view it."
                ),
                exclude_emails=[request.user.email],
            )

        output = ProjectFileDetailSerializer(project_file, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Retrieve project file",
        description="Returns details of a project file according to the authenticated user's access level.",
        tags=["Project Files"],
        responses={200: ProjectFileDetailSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        project_file = self.get_object()

        if not can_view_file(request.user, project_file):
            raise PermissionDenied("You cannot view this file.")

        serializer = ProjectFileDetailSerializer(project_file, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Update project file",
        description=(
            "Allows producers to update any file. "
            "Scriptwriters/directors can only update their own draft or rejected files."
        ),
        tags=["Project Files"],
        request=ProjectFileUpdateSerializer,
        responses={200: ProjectFileDetailSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        project_file = self.get_object()

        if not can_edit_file(request.user, project_file):
            raise PermissionDenied("You cannot edit this file.")

        serializer = ProjectFileUpdateSerializer(
            project_file,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        project_file = serializer.save()

        notify_project_team(
            self.project,
            subject=f"Project file updated: {self.project.title}",
            message=(
                f"A file has been updated in project '{self.project.title}'.\n\n"
                f"Title: {project_file.title}\n"
                f"Type: {project_file.file_type}\n"
                f"Status: {project_file.status}\n\n"
                f"Please login to view the latest information."
            ),
            exclude_emails=[request.user.email],
        )

        output = ProjectFileDetailSerializer(project_file, context={"request": request})
        return Response(output.data)

    @extend_schema(
        summary="Delete project file",
        description="Allows producers to delete any project file. File owners can delete their own draft or rejected files.",
        tags=["Project Files"],
        responses={204: OpenApiResponse(description="File deleted successfully.")},
    )
    def destroy(self, request, *args, **kwargs):
        project_file = self.get_object()

        if request.user.role != "PRODUCER":
            if project_file.uploaded_by_id != request.user.id or project_file.status not in ["DRAFT", "REJECTED"]:
                raise PermissionDenied("You cannot delete this file.")

        title = project_file.title
        project_file.delete()

        notify_project_team(
            self.project,
            subject=f"Project file deleted: {self.project.title}",
            message=(
                f"A file has been deleted from project '{self.project.title}'.\n\n"
                f"File: {title}\n\n"
                f"Production team."
            ),
            exclude_emails=[request.user.email],
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Submit file for review",
        description="Allows the owner of a draft or rejected file to submit it for producer review.",
        tags=["Script Review"],
        request=ProjectFileActionSerializer,
        responses={200: ProjectFileDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="submit-review")
    def submit_review(self, request, project_pk=None, pk=None):
        project_file = self.get_object()

        if not can_submit_file(request.user, project_file):
            raise PermissionDenied("You cannot submit this file for review.")

        project_file.status = ProjectFileStatus.PENDING_REVIEW
        project_file.submitted_at = timezone.now()
        project_file.rejection_reason = ""
        project_file.save()

        notify_project_producers(
            self.project,
            subject=f"File submitted for review: {self.project.title}",
            message=(
                f"A file has been submitted for review in project '{self.project.title}'.\n\n"
                f"Title: {project_file.title}\n"
                f"Type: {project_file.file_type}\n"
                f"Version: {project_file.version}\n"
                f"Submitted by: {request.user.full_name}\n\n"
                f"Please login to approve or reject it."
            ),
        )

        output = ProjectFileDetailSerializer(project_file, context={"request": request})
        return Response(output.data)

    @extend_schema(
        summary="Approve project file",
        description=(
            "Allows producers/admins to approve a pending file. "
            "When approved, all project members including actors receive an email notification."
        ),
        tags=["Script Review"],
        request=ProjectFileActionSerializer,
        responses={200: ProjectFileDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, project_pk=None, pk=None):
        if request.user.role != "PRODUCER":
            raise PermissionDenied("Only producers can approve files.")

        project_file = self.get_object()

        project_file.status = ProjectFileStatus.APPROVED
        project_file.reviewed_by = request.user
        project_file.reviewed_at = timezone.now()
        project_file.rejection_reason = ""
        project_file.save()

        notify_project_team(
            self.project,
            subject=f"New approved file available: {self.project.title}",
            message=(
                f"A file has been approved and is now available in project '{self.project.title}'.\n\n"
                f"Title: {project_file.title}\n"
                f"Type: {project_file.file_type}\n"
                f"Version: {project_file.version}\n\n"
                f"Please login to view it."
            ),
        )

        output = ProjectFileDetailSerializer(project_file, context={"request": request})
        return Response(output.data)

    @extend_schema(
        summary="Reject project file",
        description="Allows producers/admins to reject a pending file and provide a rejection reason.",
        tags=["Script Review"],
        request=ProjectFileRejectSerializer,
        responses={200: ProjectFileDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, project_pk=None, pk=None):
        if request.user.role != "PRODUCER":
            raise PermissionDenied("Only producers can reject files.")

        project_file = self.get_object()

        serializer = ProjectFileRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reason = serializer.validated_data["reason"]

        project_file.status = ProjectFileStatus.REJECTED
        project_file.reviewed_by = request.user
        project_file.reviewed_at = timezone.now()
        project_file.rejection_reason = reason
        project_file.save()

        send_mail(
            subject=f"Your file was rejected: {self.project.title}",
            message=(
                f"Hello {project_file.uploaded_by.full_name},\n\n"
                f"Your file submitted for project '{self.project.title}' was rejected.\n\n"
                f"Title: {project_file.title}\n"
                f"Reason: {reason}\n\n"
                f"Please update it and submit again."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[project_file.uploaded_by.email],
            fail_silently=False,
        )

        notify_project_team(
            self.project,
            subject=f"Project file review update: {self.project.title}",
            message=(
                f"A file review status has changed in project '{self.project.title}'.\n\n"
                f"Title: {project_file.title}\n"
                f"Status: REJECTED\n\n"
                f"Production team."
            ),
            exclude_emails=[project_file.uploaded_by.email],
        )

        output = ProjectFileDetailSerializer(project_file, context={"request": request})
        return Response(output.data)