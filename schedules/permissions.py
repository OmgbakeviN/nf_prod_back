from projects.models import ProjectMember


def can_access_project(user, project):
    if user.role == "PRODUCER":
        return True

    return ProjectMember.objects.filter(project=project, user=user).exists()


def can_manage_planning(user, project):
    if user.role == "PRODUCER":
        return True

    member = ProjectMember.objects.filter(project=project, user=user).first()

    if not member:
        return False

    return member.role in ["DIRECTOR", "CREW"]