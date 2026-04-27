from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import (
    UserSerializer,
    MeSerializer,
    InviteUserSerializer,
    UserUpdateSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsProducer, IsOwnerOrProducer

User = get_user_model()


class HealthCheckAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Health check",
        description="Public endpoint used to verify that the backend API is running correctly.",
        tags=["System"],
        responses={200: OpenApiResponse(description="API is running correctly.")},
    )
    def get(self, request):
        return Response({
            "status": "ok",
            "message": "Production Platform API is running."
        })


class LoginAPIView(TokenObtainPairView):
    @extend_schema(
        summary="Login user",
        description="Authenticates a user using email and password. Returns access and refresh JWT tokens.",
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshTokenAPIView(TokenRefreshView):
    @extend_schema(
        summary="Refresh access token",
        description="Generates a new access token using a valid refresh token.",
        tags=["Authentication"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get authenticated user",
        description="Returns the profile of the currently authenticated user.",
        tags=["Authentication"],
        responses={200: MeSerializer},
    )
    def get(self, request):
        serializer = MeSerializer(request.user, context={"request": request})
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "invite":
            return InviteUserSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ["retrieve", "partial_update", "update"]:
            return [IsAuthenticated(), IsOwnerOrProducer()]
        return [IsAuthenticated(), IsProducer()]

    @extend_schema(
        summary="List users",
        description="Allows producers/admins to list all users registered on the platform.",
        tags=["Users"],
        responses={200: UserSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve user",
        description="Returns the details of a user. Producers can access all users. Normal users can only access their own profile.",
        tags=["Users"],
        responses={200: UserSerializer},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update user",
        description="Updates user information. Producers can update roles and status.",
        tags=["Users"],
        request=UserUpdateSerializer,
        responses={200: UserSerializer},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete user",
        description="Allows producers/admins to delete a user from the platform.",
        tags=["Users"],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary="Invite user",
        description="Allows a producer/admin to invite a new user to the platform. The system creates an account with a temporary password and sends an email notification.",
        tags=["Users"],
        request=InviteUserSerializer,
        responses={201: UserSerializer},
    )
    @action(detail=False, methods=["post"], url_path="invite")
    def invite(self, request):
        serializer = InviteUserSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        temporary_password = user.temporary_password

        send_mail(
            subject="You have been invited to Production Platform",
            message=(
                f"Hello {user.full_name},\n\n"
                f"You have been invited to join the production platform.\n\n"
                f"Login email: {user.email}\n"
                f"Temporary password: {temporary_password}\n\n"
                f"Please login and change your password later."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        output_serializer = UserSerializer(user, context={"request": request})
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class ProfileUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        summary="Update authenticated user profile",
        description="Allows the authenticated user to update their profile information and avatar.",
        tags=["Authentication"],
        request=ProfileUpdateSerializer,
        responses={200: MeSerializer},
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        output = MeSerializer(request.user, context={"request": request})
        return Response(output.data)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Change password",
        description="Allows the authenticated user to change their password using their current password.",
        tags=["Authentication"],
        request=ChangePasswordSerializer,
        responses={200: OpenApiResponse(description="Password changed successfully.")},
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "detail": "Password changed successfully."
        }, status=status.HTTP_200_OK)