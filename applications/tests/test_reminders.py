from django.contrib.auth.models import User
from django.test import TestCase
from datetime import date


from applications.models import ApplicationEvent, JobApplication, Reminder, ReminderRule
from applications.services.reminders import generate_reminders_for_application

class ReminderRuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="testpass123"
        )

        self.application = JobApplication.objects.create(
            user=self.user,
            company_name="Muster GmbH",
            job_title="Backend Developer",
            status=JobApplication.Status.APPLIED,
            applied_at=date(2026, 8, 1),
        )

        self.follow_up_rule = ReminderRule.objects.create(
            name="Send follow-up",
            trigger_status=JobApplication.Status.APPLIED,
            anchor_type=ReminderRule.AnchorType.APPLIED_AT,
            offset_direction=ReminderRule.OffsetDirection.AFTER,
            offset_days=14,
            title_template="Send follow-up for {job_title} at {company_name}",
        )

    # Applied creates follow-up reminder
    def test_applied_status_generates_follow_up_reminder(self):
        reminders = generate_reminders_for_application(self.application)

        self.assertEqual(len(reminders), 1)

        reminder = reminders[0]

        self.assertEqual(reminder.application, self.application)
        self.assertEqual(reminder.rule, self.follow_up_rule)
        self.assertEqual(reminder.status, Reminder.Status.OPEN)
        self.assertIn("Backend Developer", reminder.title)
        self.assertIn("Muster GmbH", reminder.title)

        expected_due_date = date(2026, 8, 15)
        self.assertEqual(reminder.due_at.date(), expected_due_date)

    # Missing anchor skips reminder
    def test_missing_anchor_does_not_create_reminder(self):
        self.application.applied_at = None
        self.application.save()

        reminders = generate_reminders_for_application(self.application)

        self.assertEqual(len(reminders), 0)
        self.assertEqual(Reminder.objects.count(), 0)

    # Duplicate reminder is not created
    def test_duplicate_open_reminder_is_not_created(self):
        generate_reminders_for_application(self.application)
        generate_reminders_for_application(self.application)

        reminders = Reminder.objects.filter(
            application=self.application,
            rule=self.follow_up_rule,
            status=Reminder.Status.OPEN,
        )

        self.assertEqual(reminders.count(), 1)

    # Reminder created event is logged
    def test_reminder_created_event_is_logged(self):
        generate_reminders_for_application(self.application)

        event = ApplicationEvent.objects.filter(
            application=self.application,
            event_type=ApplicationEvent.EventType.REMINDER_CREATED,
        ).first()

        self.assertIsNotNone(event)
        self.assertIn("Reminder created", event.description)