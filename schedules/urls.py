from django.urls import path

from .views import ShootingLocationViewSet, ScheduleEventViewSet


location_list = ShootingLocationViewSet.as_view({
    "get": "list",
    "post": "create",
})

location_detail = ShootingLocationViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "delete": "destroy",
})

schedule_list = ScheduleEventViewSet.as_view({
    "get": "list",
    "post": "create",
})

schedule_detail = ScheduleEventViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "delete": "destroy",
})


urlpatterns = [
    path(
        "projects/<int:project_pk>/locations/",
        location_list,
        name="project-locations-list",
    ),
    path(
        "projects/<int:project_pk>/locations/<int:pk>/",
        location_detail,
        name="project-locations-detail",
    ),

    path(
        "projects/<int:project_pk>/schedule/",
        schedule_list,
        name="project-schedule-list",
    ),
    path(
        "projects/<int:project_pk>/schedule/<int:pk>/",
        schedule_detail,
        name="project-schedule-detail",
    ),
]