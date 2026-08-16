from django.utils import timezone
from .models import JobApplication, ApplicationEvent
from django.db import transaction

# this is the event logging and status change function of job applications
@transaction.atomic
def change_application_status(application : JobApplication, new_status : str):
    old_status = application.status

    if old_status == new_status:
        return application

    valid_statuses = [choice[0] for choice in JobApplication.Status.choices]

    if new_status not in valid_statuses:
        raise ValueError("Invalid status")

    application.status = new_status

    # set important date fields automatically
    if new_status == JobApplication.Status.APPLIED and not application.applied_at:
        application.applied_at = timezone.localdate()

    if (new_status == JobApplication.Status.INTERVIEW_COMPLETED and not application.interview_completed_at):
        application.interview_completed_at = timezone.localdate()

    application.save()

    ApplicationEvent.objects.create(
        application=application,
        event_type=ApplicationEvent.EventType.STATUS_CHANGED,
        old_status=old_status,
        new_status=new_status,
        description=(
            f"Status changed from "
            f"{JobApplication.Status(old_status).label} to "
            f"{JobApplication.Status(new_status).label}."
        )
    )

    return application