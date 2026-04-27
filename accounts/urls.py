from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    HealthCheckAPIView,
    LoginAPIView,
    RefreshTokenAPIView,
    MeAPIView,
    UserViewSet,
    ProfileUpdateAPIView,
    ChangePasswordAPIView,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("health/", HealthCheckAPIView.as_view(), name="health-check"),

    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("auth/refresh/", RefreshTokenAPIView.as_view(), name="token-refresh"),
    path("auth/me/", MeAPIView.as_view(), name="me"),

    path("", include(router.urls)),

    path("auth/profile/", ProfileUpdateAPIView.as_view(), name="profile-update"),
    path("auth/change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
]