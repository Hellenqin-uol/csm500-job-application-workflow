from datetime import datetime, time, timedelta
from django.utils import timezone
from applications.models import ApplicationEvent, JobApplication, Reminder, ReminderRule

def cancel_open_rule_based_reminders(application):
    Reminder.objects.filter(
        application=application,
        status=Reminder.Status.OPEN,
        source=Reminder.Source.RULE,
    ).update(
        status=Reminder.Status.CANCELLED
    )


def get_status_changed_at(application):
    event = application.events.filter(
        event_type=ApplicationEvent.EventType.STATUS_CHANGED,
        new_status=application.status,
    ).order_by("-created_at").first()

    if event:
        return event.created_at

    return timezone.now()


def date_to_datetime(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        if timezone.is_naive(value):
            return timezone.make_aware(value)
        return value

    return timezone.make_aware(
        datetime.combine(value, time(hour=9, minute=0))
    )


def resolve_anchor_datetime(application, rule):
    if rule.anchor_type == ReminderRule.AnchorType.APPLICATION_DEADLINE:
        return date_to_datetime(application.application_deadline)

    if rule.anchor_type == ReminderRule.AnchorType.APPLIED_AT:
        return date_to_datetime(application.applied_at)

    if rule.anchor_type == ReminderRule.AnchorType.INTERVIEW_AT:
        return date_to_datetime(application.interview_at)

    if rule.anchor_type == ReminderRule.AnchorType.INTERVIEW_COMPLETED_AT:
        return date_to_datetime(application.interview_completed_at)

    if rule.anchor_type == ReminderRule.AnchorType.OFFER_DEADLINE:
        return date_to_datetime(application.offer_deadline)

    if rule.anchor_type == ReminderRule.AnchorType.STATUS_CHANGED_AT:
        return get_status_changed_at(application)

    return None


def apply_offset(anchor, rule):
    delta = timedelta(days=rule.offset_days)

    if rule.offset_direction == ReminderRule.OffsetDirection.BEFORE:
        return anchor - delta

    return anchor + delta


def render_reminder_title(application, rule):
    return rule.title_template.format(
        job_title=application.job_title,
        company_name=application.company_name,
        status=application.get_status_display(),
    )


def generate_reminders_for_application(application):
    if application.status in [
        JobApplication.Status.REJECTED,
        JobApplication.Status.WITHDRAWN,
        JobApplication.Status.ARCHIVED,
    ]:
        cancel_open_rule_based_reminders(application)
        return []

    rules = ReminderRule.objects.filter(
        trigger_status=application.status,
        is_active=True,
    )

    created_reminders = []

    for rule in rules:
        anchor = resolve_anchor_datetime(application, rule)

        if not anchor:
            continue

        due_at = apply_offset(anchor, rule)
        title = render_reminder_title(application, rule)

        exists = Reminder.objects.filter(
            application=application,
            rule=rule,
            status=Reminder.Status.OPEN,
        ).exists()

        if exists:
            continue

        reminder = Reminder.objects.create(
            application=application,
            rule=rule,
            title=title,
            due_at=due_at,
            source=Reminder.Source.RULE,
        )

        ApplicationEvent.objects.create(
            application=application,
            event_type=ApplicationEvent.EventType.REMINDER_CREATED,
            description=f"Reminder created: {title}"
        )

        created_reminders.append(reminder)

    return created_reminders