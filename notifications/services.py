from django.conf import settings
from django.core.mail import send_mail

from projects.models import ProjectMember
from .models import Notification


def get_project_members(project):
    return (
        ProjectMember.objects
        .filter(project=project)
        .select_related("user")
    )


def notify_user(user, title, message, notification_type="SYSTEM", related_project=None, related_url="", send_email=True):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=notification_type,
        related_project_id=related_project.id if related_project else None,
        related_url=related_url or "",
    )

    if send_email and user.email:
        send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )


def notify_project_team(project, title, message, notification_type="PROJECT", related_url="", exclude_user_ids=None, send_email=True):
    exclude_user_ids = exclude_user_ids or []

    members = get_project_members(project)

    notified_user_ids = set()

    for member in members:
        user = member.user

        if user.id in exclude_user_ids:
            continue

        if user.id in notified_user_ids:
            continue

        notify_user(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            related_project=project,
            related_url=related_url,
            send_email=send_email,
        )

        notified_user_ids.add(user.id)