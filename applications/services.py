from django.utils import timezone
from .models import JobApplication, ApplicationEvent
from django.db import transaction
from django.utils.dateparse import parse_date, parse_datetime
from django.core.exceptions import ValidationError

# helpfer function for parse dates
def parse_required_date(value, field_label):
    parsed = parse_date(value)

    if parsed is None:
        raise ValidationError(f"Invalid {field_label}.")

    return parsed

# helper function for parsing datetimes
def parse_required_datetime(value, field_label):
    parsed = parse_datetime(value)

    if parsed is None:
        raise ValidationError(f"Invalid {field_label}.")

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)

    return parsed

# this is the event logging and status change function of job applications
@transaction.atomic
def change_application_status(application : JobApplication, new_status : str, transition_data: dict | None = None) -> JobApplication:
    old_status = application.status

    if old_status == new_status:
        return application

    valid_statuses = [choice[0] for choice in JobApplication.Status.choices]

    if new_status not in valid_statuses:
        raise ValueError("Invalid status")

    application.status = new_status

    # Applied: default today if no value provided
    if new_status == JobApplication.Status.APPLIED:
        applied_at_value = transition_data.get("applied_at")
        if applied_at_value:
            application.applied_at = parse_required_date(applied_at_value, "applied date")
        elif not application.applied_at:
            application.applied_at = timezone.localdate()

    # Interview Scheduled: must have interview_at
    elif new_status == JobApplication.Status.INTERVIEW_SCHEDULED:
        interview_at_value = transition_data.get("interview_at")

        if interview_at_value:
            application.interview_at = parse_required_datetime(
                interview_at_value,
                "interview date and time"
            )
        elif not application.interview_at:
            raise ValidationError("Interview date and time is required.")

    # Interview Completed: default today if no value provided
    elif new_status == JobApplication.Status.INTERVIEW_COMPLETED:
        completed_at_value = transition_data.get("interview_completed_at")

        if completed_at_value:
            application.interview_completed_at = parse_required_date(
                completed_at_value,
                "interview completed date"
            )
        elif not application.interview_completed_at:
            application.interview_completed_at = timezone.localdate()

    # Offer Received: must have offer_deadline
    elif new_status == JobApplication.Status.OFFER_RECEIVED:
        offer_deadline_value = transition_data.get("offer_deadline")

        if offer_deadline_value:
            application.offer_deadline = parse_required_date(
                offer_deadline_value,
                "offer deadline"
            )
        elif not application.offer_deadline:
            raise ValidationError("Offer deadline is required.")

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