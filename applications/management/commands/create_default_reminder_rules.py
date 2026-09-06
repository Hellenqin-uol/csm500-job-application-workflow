from django.core.management.base import BaseCommand

from applications.models import JobApplication, ReminderRule

DEFAULT_REMINDER_RULES = [
    {
        "name": "Review job before deadline",
        "trigger_status": JobApplication.Status.INTERESTED,
        "anchor_type": ReminderRule.AnchorType.APPLICATION_DEADLINE,
        "offset_direction": ReminderRule.OffsetDirection.BEFORE,
        "offset_days": 3,
        "title_template": "Review {job_title} at {company_name} before the application deadline",
    },
    {
        "name": "Submit application",
        "trigger_status": JobApplication.Status.PREPARING,
        "anchor_type": ReminderRule.AnchorType.APPLICATION_DEADLINE,
        "offset_direction": ReminderRule.OffsetDirection.BEFORE,
        "offset_days": 1,
        "title_template": "Submit application for {job_title} at {company_name}",
    },
    {
        "name": "Send follow-up",
        "trigger_status": JobApplication.Status.APPLIED,
        "anchor_type": ReminderRule.AnchorType.APPLIED_AT,
        "offset_direction": ReminderRule.OffsetDirection.AFTER,
        "offset_days": 14,
        "title_template": "Send follow-up for {job_title} at {company_name}",
    },
    {
        "name": "Check for reply",
        "trigger_status": JobApplication.Status.WAITING_FOR_REPLY,
        "anchor_type": ReminderRule.AnchorType.STATUS_CHANGED_AT,
        "offset_direction": ReminderRule.OffsetDirection.AFTER,
        "offset_days": 10,
        "title_template": "Check for reply from {company_name} regarding {job_title}",
    },
    {
        "name": "Prepare interview",
        "trigger_status": JobApplication.Status.INTERVIEW_SCHEDULED,
        "anchor_type": ReminderRule.AnchorType.INTERVIEW_AT,
        "offset_direction": ReminderRule.OffsetDirection.BEFORE,
        "offset_days": 1,
        "title_template": "Prepare interview for {job_title} at {company_name}",
    },
    {
        "name": "Send thank-you/follow-up",
        "trigger_status": JobApplication.Status.INTERVIEW_COMPLETED,
        "anchor_type": ReminderRule.AnchorType.INTERVIEW_COMPLETED_AT,
        "offset_direction": ReminderRule.OffsetDirection.AFTER,
        "offset_days": 2,
        "title_template": "Send post-interview follow-up for {job_title} at {company_name}",
    },
    {
        "name": "Ask for decision update",
        "trigger_status": JobApplication.Status.WAITING_FOR_DECISION,
        "anchor_type": ReminderRule.AnchorType.STATUS_CHANGED_AT,
        "offset_direction": ReminderRule.OffsetDirection.AFTER,
        "offset_days": 7,
        "title_template": "Ask for decision update from {company_name} regarding {job_title}",
    },
    {
        "name": "Review offer",
        "trigger_status": JobApplication.Status.OFFER_RECEIVED,
        "anchor_type": ReminderRule.AnchorType.OFFER_DEADLINE,
        "offset_direction": ReminderRule.OffsetDirection.BEFORE,
        "offset_days": 2,
        "title_template": "Review offer from {company_name} before the deadline",
    },
]

class Command(BaseCommand):
    help = "Seed default reminder rules"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for rule_data in DEFAULT_REMINDER_RULES:
            rule, created = ReminderRule.objects.update_or_create(
                name=rule_data["name"],
                trigger_status=rule_data["trigger_status"],
                defaults=rule_data,
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Reminder rules inserted. Created: {created_count}, updated: {updated_count}"
            )
        )