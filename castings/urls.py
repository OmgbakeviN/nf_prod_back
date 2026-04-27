from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CastingViewSet, PublicCastingViewSet, ApplicationViewSet

router = DefaultRouter()
router.register("castings", CastingViewSet, basename="castings")
router.register("public/castings", PublicCastingViewSet, basename="public-castings")
router.register("applications", ApplicationViewSet, basename="applications")

urlpatterns = [
    path("", include(router.urls)),
]