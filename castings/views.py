from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from django.utils.crypto import get_random_string

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Casting, Application, ApplicationStatus
from .serializers import (
    CastingListSerializer,
    CastingCreateUpdateSerializer,
    CastingDetailSerializer,
    PublicCastingSerializer,
    ApplicationCreateSerializer,
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationStatusUpdateSerializer,
)
from .permissions import IsProducer

User = get_user_model()

class CastingViewSet(viewsets.ModelViewSet):
    queryset = Casting.objects.annotate(applications_count=Count("applications"))
    permission_classes = [IsAuthenticated, IsProducer]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CastingCreateUpdateSerializer
        if self.action == "retrieve":
            return CastingDetailSerializer
        return CastingListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        summary="List castings",
        description="Allows producers/admins to list all casting forms created on the platform.",
        tags=["Castings"],
        responses={200: CastingListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create casting",
        description="Allows a producer/admin to create a public casting form.",
        tags=["Castings"],
        request=CastingCreateUpdateSerializer,
        responses={201: CastingDetailSerializer},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve casting",
        description="Returns details about a casting form including application count.",
        tags=["Castings"],
        responses={200: CastingDetailSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update casting",
        description="Allows a producer/admin to update a casting form.",
        tags=["Castings"],
        request=CastingCreateUpdateSerializer,
        responses={200: CastingDetailSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete casting",
        description="Allows a producer/admin to delete a casting form.",
        tags=["Castings"],
        responses={204: OpenApiResponse(description="Casting deleted successfully.")},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class PublicCastingViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        summary="Retrieve public casting",
        description="Public endpoint used by candidates to view an open casting form before applying.",
        tags=["Public Castings"],
        responses={200: PublicCastingSerializer},
    )
    def retrieve(self, request, pk=None):
        try:
            casting = Casting.objects.get(
                pk=pk,
                is_public=True,
                status="OPEN",
            )
        except Casting.DoesNotExist:
            return Response(
                {"detail": "Casting not found or not open."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PublicCastingSerializer(casting)
        return Response(serializer.data)

    @extend_schema(
        summary="Submit casting application",
        description="Public endpoint used by actors to submit a casting application with personal information, headshot and video.",
        tags=["Public Castings"],
        request=ApplicationCreateSerializer,
        responses={201: ApplicationDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="apply")
    def apply(self, request, pk=None):
        try:
            casting = Casting.objects.get(
                pk=pk,
                is_public=True,
                status="OPEN",
            )
        except Casting.DoesNotExist:
            return Response(
                {"detail": "Casting not found or not open."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save(casting=casting)

        send_mail(
            subject="Casting application received",
            message=(
                f"Hello {application.full_name},\n\n"
                f"Your application for '{casting.title}' has been received.\n"
                f"We will contact you after review.\n\n"
                f"Thank you."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.email],
            fail_silently=False,
        )

        if casting.created_by.email:
            send_mail(
                subject="New casting application",
                message=(
                    f"A new application has been submitted.\n\n"
                    f"Casting: {casting.title}\n"
                    f"Candidate: {application.full_name}\n"
                    f"Email: {application.email}\n"
                    f"Phone: {application.phone}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[casting.created_by.email],
                fail_silently=False,
            )

        output = ApplicationDetailSerializer(application, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class ApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Application.objects.select_related("casting", "reviewed_by").all()
    permission_classes = [IsAuthenticated, IsProducer]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ApplicationDetailSerializer
        return ApplicationListSerializer

    @extend_schema(
        summary="List applications",
        description="Allows producers/admins to list all casting applications.",
        tags=["Applications"],
        responses={200: ApplicationListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        casting_id = request.query_params.get("casting")
        status_filter = request.query_params.get("status")

        queryset = self.get_queryset()

        if casting_id:
            queryset = queryset.filter(casting_id=casting_id)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="Retrieve application",
        description="Allows producers/admins to view complete details of a casting application.",
        tags=["Applications"],
        responses={200: ApplicationDetailSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def _update_status(self, request, pk, new_status, email_subject, email_message):
        application = self.get_object()
        serializer = ApplicationStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        note = serializer.validated_data.get("note", "")

        application.status = new_status
        application.admin_note = note
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()

        send_mail(
            subject=email_subject,
            message=email_message(application, note),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.email],
            fail_silently=False,
        )

        output = ApplicationDetailSerializer(application, context={"request": request})
        return Response(output.data)

    @extend_schema(
    summary="Accept application",
    description=(
        "Allows a producer/admin to accept a candidate application. "
        "When accepted, the system creates an actor user account if it does not already exist, "
        "then sends the candidate an email with login credentials."
    ),
    tags=["Applications"],
    request=ApplicationStatusUpdateSerializer,
    responses={200: ApplicationDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        application = self.get_object()

        serializer = ApplicationStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        note = serializer.validated_data.get("note", "")

        application.status = ApplicationStatus.ACCEPTED
        application.admin_note = note
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()

        existing_user = User.objects.filter(email=application.email).first()

        if existing_user:
            send_mail(
                subject="Casting application accepted",
                message=(
                    f"Hello {application.full_name},\n\n"
                    f"Congratulations! Your application for '{application.casting.title}' has been accepted.\n\n"
                    f"Your account already exists on the platform. You can login using your existing credentials.\n\n"
                    f"{note}\n\n"
                    f"Production team."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                fail_silently=False,
            )
        else:
            temporary_password = get_random_string(10)

            user = User.objects.create_user(
                email=application.email,
                password=temporary_password,
                full_name=application.full_name,
                phone=application.phone,
                role="ACTOR",
                invited_by=request.user,
                is_active=True,
            )

            send_mail(
                subject="Casting application accepted - Your account has been created",
                message=(
                    f"Hello {application.full_name},\n\n"
                    f"Congratulations! Your application for '{application.casting.title}' has been accepted.\n\n"
                    f"An account has been created for you on the production platform.\n\n"
                    f"Login email: {user.email}\n"
                    f"Temporary password: {temporary_password}\n\n"
                    f"Please login and keep your credentials safe.\n\n"
                    f"{note}\n\n"
                    f"Production team."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                fail_silently=False,
            )

        output = ApplicationDetailSerializer(application, context={"request": request})
        return Response(output.data)

    @extend_schema(
        summary="Reject application",
        description="Allows a producer/admin to reject a candidate application. The candidate receives an email notification.",
        tags=["Applications"],
        request=ApplicationStatusUpdateSerializer,
        responses={200: ApplicationDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        return self._update_status(
            request,
            pk,
            ApplicationStatus.REJECTED,
            "Casting application update",
            lambda app, note: (
                f"Hello {app.full_name},\n\n"
                f"Thank you for applying for '{app.casting.title}'.\n"
                f"Unfortunately, your application was not selected this time.\n\n"
                f"{note}\n\n"
                f"Production team."
            ),
        )

    @extend_schema(
        summary="Request more information",
        description="Allows a producer/admin to request additional information from a candidate.",
        tags=["Applications"],
        request=ApplicationStatusUpdateSerializer,
        responses={200: ApplicationDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="request-info")
    def request_info(self, request, pk=None):
        return self._update_status(
            request,
            pk,
            ApplicationStatus.NEEDS_MORE_INFO,
            "More information required",
            lambda app, note: (
                f"Hello {app.full_name},\n\n"
                f"The production team needs more information about your application for '{app.casting.title}'.\n\n"
                f"{note}\n\n"
                f"Production team."
            ),
        )