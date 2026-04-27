from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet, ProjectMemberViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="projects")

project_member_list = ProjectMemberViewSet.as_view({
    "get": "list",
    "post": "create",
})

project_member_detail = ProjectMemberViewSet.as_view({
    "patch": "partial_update",
    "delete": "destroy",
})

urlpatterns = [
    path("", include(router.urls)),

    path(
        "projects/<int:project_pk>/members/",
        project_member_list,
        name="project-members-list",
    ),
    path(
        "projects/<int:project_pk>/members/<int:pk>/",
        project_member_detail,
        name="project-members-detail",
    ),
]