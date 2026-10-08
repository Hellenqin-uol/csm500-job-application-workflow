from django.core.management.base import BaseCommand

from applications.models import ReminderRule

from applications.default_reminder_rules import DEFAULT_REMINDER_RULES
"""
Management command for creating the default reminder rule set.
"""

class Command(BaseCommand):
    help = "Create or update default reminder rules"

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