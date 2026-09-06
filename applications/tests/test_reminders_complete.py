
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone


from applications.models import ApplicationEvent, JobApplication, Reminder, 

class ReminderCompletionTests(TestCase):
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
        )

        self.reminder = Reminder.objects.create(
            application=self.application,
            title="Send follow-up",
            due_at=timezone.now(),
            status=Reminder.Status.OPEN,
            source=Reminder.Source.RULE,
        )

    # Complete reminder sets status done
    def test_complete_reminder_marks_done(self):
        self.client.login(username="alice", password="testpass123")

        url = reverse(
            "applications:reminder_complete",
            kwargs={"pk": self.reminder.pk}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)

        self.reminder.refresh_from_db()

        self.assertEqual(self.reminder.status, Reminder.Status.DONE)
        self.assertIsNotNone(self.reminder.completed_at)

    # Complete reminder logs event
    def test_complete_reminder_logs_event(self):
        self.client.login(username="alice", password="testpass123")

        url = reverse(
            "applications:reminder_complete",
            kwargs={"pk": self.reminder.pk}
        )

        self.client.post(url)

        event = ApplicationEvent.objects.filter(
            application=self.application,
            event_type=ApplicationEvent.EventType.REMINDER_COMPLETED,
        ).first()

        self.assertIsNotNone(event)
        self.assertIn("Reminder completed", event.description)

    # Other user cannot complete reminder
    def test_other_user_cannot_complete_reminder(self):
        other_user = User.objects.create_user(
            username="bob",
            password="testpass123"
        )

        self.client.login(username="bob", password="testpass123")

        url = reverse(
            "applications:reminder_complete",
            kwargs={"pk": self.reminder.pk}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)

        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.status, Reminder.Status.OPEN)