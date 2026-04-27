from django.urls import path

from .views import ProjectFileViewSet

project_file_list = ProjectFileViewSet.as_view({
    "get": "list",
    "post": "create",
})

project_file_detail = ProjectFileViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "delete": "destroy",
})

project_file_submit_review = ProjectFileViewSet.as_view({
    "post": "submit_review",
})

project_file_approve = ProjectFileViewSet.as_view({
    "post": "approve",
})

project_file_reject = ProjectFileViewSet.as_view({
    "post": "reject",
})

urlpatterns = [
    path(
        "projects/<int:project_pk>/files/",
        project_file_list,
        name="project-files-list",
    ),
    path(
        "projects/<int:project_pk>/files/<int:pk>/",
        project_file_detail,
        name="project-files-detail",
    ),
    path(
        "projects/<int:project_pk>/files/<int:pk>/submit-review/",
        project_file_submit_review,
        name="project-files-submit-review",
    ),
    path(
        "projects/<int:project_pk>/files/<int:pk>/approve/",
        project_file_approve,
        name="project-files-approve",
    ),
    path(
        "projects/<int:project_pk>/files/<int:pk>/reject/",
        project_file_reject,
        name="project-files-reject",
    ),
]