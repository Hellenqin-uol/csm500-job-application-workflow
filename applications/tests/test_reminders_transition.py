import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from datetime import date, timedelta

from applications.models import JobApplication, Reminder, ReminderRule
from applications.services.reminders import generate_reminders_for_application


class ReminderWorkflowIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="testpass123"
        )

        self.application = JobApplication.objects.create(
            user=self.user,
            company_name="Muster GmbH",
            job_title="Backend Developer",
            status=JobApplication.Status.INTERESTED,
        )

        self.rule = ReminderRule.objects.create(
            name="Send follow-up",
            trigger_status=JobApplication.Status.APPLIED,
            anchor_type=ReminderRule.AnchorType.APPLIED_AT,
            offset_direction=ReminderRule.OffsetDirection.AFTER,
            offset_days=14,
            title_template="Send follow-up for {job_title} at {company_name}",
        )

    # Drag-style status update creates reminder
    def test_status_update_to_applied_creates_reminder(self):
        self.client.login(username="alice", password="testpass123")

        url = reverse(
            "applications:application_update_status",
            kwargs={"pk": self.application.pk}
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "status": JobApplication.Status.APPLIED,
                "applied_at": "2026-08-01",
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        self.application.refresh_from_db()

        self.assertEqual(self.application.status, JobApplication.Status.APPLIED)
        self.assertEqual(self.application.applied_at, date(2026, 8, 1))

        reminder = Reminder.objects.get(application=self.application)
        self.assertEqual(reminder.status, Reminder.Status.OPEN)
        self.assertEqual(reminder.due_at.date(), date(2026, 8, 15))

    # Interview Scheduled creates preparation reminder
    def test_status_update_to_interview_scheduled_creates_reminder(self):
        self.client.login(username="alice", password="testpass123")

        ReminderRule.objects.create(
            name="Prepare interview",
            trigger_status=JobApplication.Status.INTERVIEW_SCHEDULED,
            anchor_type=ReminderRule.AnchorType.INTERVIEW_AT,
            offset_direction=ReminderRule.OffsetDirection.BEFORE,
            offset_days=1,
            title_template="Prepare interview for {job_title} at {company_name}",
        )

        url = reverse(
            "applications:application_update_status",
            kwargs={"pk": self.application.pk}
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "status": JobApplication.Status.INTERVIEW_SCHEDULED,
                "interview_at": "2026-08-10T10:00",
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.INTERVIEW_SCHEDULED
        )

        reminder = Reminder.objects.get(application=self.application)
        self.assertEqual(reminder.status, Reminder.Status.OPEN)
        self.assertEqual(reminder.due_at.date(), date(2026, 8, 9))

    # Offer Received creates offer reminder
    def test_status_update_to_offer_received_creates_reminder(self):
        self.client.login(username="alice", password="testpass123")

        ReminderRule.objects.create(
            name="Review offer",
            trigger_status=JobApplication.Status.OFFER_RECEIVED,
            anchor_type=ReminderRule.AnchorType.OFFER_DEADLINE,
            offset_direction=ReminderRule.OffsetDirection.BEFORE,
            offset_days=2,
            title_template="Review offer from {company_name} before the deadline",
        )

        url = reverse(
            "applications:application_update_status",
            kwargs={"pk": self.application.pk}
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "status": JobApplication.Status.OFFER_RECEIVED,
                "offer_deadline": "2026-08-20",
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.OFFER_RECEIVED
        )

        reminder = Reminder.objects.get(application=self.application)
        self.assertEqual(reminder.status, Reminder.Status.OPEN)
        self.assertEqual(reminder.due_at.date(), date(2026, 8, 18))

    # Status transition cancels previous rule-based reminders (moving items on kanban baord)
    def test_status_change_cancels_previous_rule_based_reminders(self):
        old_reminder = Reminder.objects.create(
            application=self.application,
            rule=self.rule,
            title="Old reminder",
            due_at=timezone.now() + timedelta(days=1),
            status=Reminder.Status.OPEN,
            source=Reminder.Source.RULE,
        )

        self.client.login(username="alice", password="testpass123")

        url = reverse(
            "applications:application_update_status",
            kwargs={"pk": self.application.pk}
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "status": JobApplication.Status.REJECTED,
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        old_reminder.refresh_from_db()
        self.assertEqual(old_reminder.status, Reminder.Status.CANCELLED)

    # Terminal state does not create reminders
    def test_terminal_status_does_not_create_new_reminders(self):
        self.application.status = JobApplication.Status.REJECTED
        self.application.save()

        reminders = generate_reminders_for_application(self.application)

        self.assertEqual(len(reminders), 0)