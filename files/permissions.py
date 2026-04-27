from rest_framework.permissions import BasePermission
from projects.models import ProjectMember


class CanAccessProjectFiles(BasePermission):
    message = "You do not have access to this project's files."

    def has_permission(self, request, view):
        project = getattr(view, "project", None)

        if not project:
            return True

        if request.user.role == "PRODUCER":
            return True

        return ProjectMember.objects.filter(
            project=project,
            user=request.user,
        ).exists()


def get_project_role(user, project):
    member = ProjectMember.objects.filter(project=project, user=user).first()
    return member.role if member else None


def can_upload_file(user, project):
    if user.role == "PRODUCER":
        return True

    project_role = get_project_role(user, project)

    return project_role in [
        "SCRIPTWRITER",
        "DIRECTOR",
        "CREW",
    ]


def can_edit_file(user, project_file):
    if user.role == "PRODUCER":
        return True

    if project_file.uploaded_by_id != user.id:
        return False

    return project_file.status in ["DRAFT", "REJECTED"]


def can_submit_file(user, project_file):
    if user.role == "PRODUCER":
        return False

    if project_file.uploaded_by_id != user.id:
        return False

    return project_file.status in ["DRAFT", "REJECTED"]


def can_view_file(user, project_file):
    if user.role == "PRODUCER":
        return True

    project_role = get_project_role(user, project_file.project)

    if not project_role:
        return False

    if project_role == "ACTOR":
        return project_file.status == "APPROVED"

    if project_role in ["SCRIPTWRITER", "DIRECTOR", "CREW", "CAMERAMAN", "EDITOR"]:
        if project_file.status == "APPROVED":
            return True

        return project_file.uploaded_by_id == user.id

    return False