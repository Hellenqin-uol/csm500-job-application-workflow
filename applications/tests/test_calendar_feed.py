from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from datetime import timedelta

from applications.models import CalendarFeed, JobApplication, Reminder

class CalendarFeedTests(TestCase):
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

        self.feed = CalendarFeed.objects.create(
            user=self.user,
            is_enabled=True,
        )

        self.open_reminder = Reminder.objects.create(
            application=self.application,
            title="Send follow-up",
            due_at=timezone.now() + timedelta(days=1),
            status=Reminder.Status.OPEN,
        )

    def get_feed_url(self, token=None):
        return reverse(
            "applications:reminder_calendar_feed",
            kwargs={"token": token or self.feed.token}
        )

# Enabled feed returns ICS
    def test_enabled_calendar_feed_returns_ics(self):
        response = self.client.get(self.get_feed_url())

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/calendar", response["Content-Type"])
        self.assertContains(response, "BEGIN:VCALENDAR")
        self.assertContains(response, "END:VCALENDAR")

# Feed contains open reminders
    def test_calendar_feed_contains_open_reminder(self):
        response = self.client.get(self.get_feed_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Send follow-up")
        self.assertContains(response, "Backend Developer")
        self.assertContains(response, "Muster GmbH")

# Feed excludes completed reminders
    def test_calendar_feed_excludes_done_reminders(self):
        Reminder.objects.create(
            application=self.application,
            title="Completed reminder",
            due_at=timezone.now() + timedelta(days=2),
            status=Reminder.Status.DONE,
        )

        response = self.client.get(self.get_feed_url())

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Completed reminder")

# Feed excludes cancelled reminders
    def test_calendar_feed_excludes_cancelled_reminders(self):
        Reminder.objects.create(
            application=self.application,
            title="Cancelled reminder",
            due_at=timezone.now() + timedelta(days=2),
            status=Reminder.Status.CANCELLED,
        )

        response = self.client.get(self.get_feed_url())

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Cancelled reminder")

#  Invalid token returns 404
    def test_invalid_calendar_feed_token_returns_404(self):
        response = self.client.get(
            self.get_feed_url(token="invalid-token")
        )

        self.assertEqual(response.status_code, 404)

# Disabled feed returns 404
    def test_disabled_calendar_feed_returns_404(self):
        self.feed.is_enabled = False
        self.feed.save()

        response = self.client.get(self.get_feed_url())

        self.assertEqual(response.status_code, 404)

# Reset token invalidates old URL
    def test_reset_calendar_feed_token_invalidates_old_url(self):
        old_token = self.feed.token

        self.client.login(username="alice", password="testpass123")

        response = self.client.post(
            reverse("applications:calendar_feed_reset")
        )

        self.assertEqual(response.status_code, 302)

        self.feed.refresh_from_db()
        new_token = self.feed.token

        self.assertNotEqual(old_token, new_token)

        old_response = self.client.get(self.get_feed_url(token=old_token))
        new_response = self.client.get(self.get_feed_url(token=new_token))

        self.assertEqual(old_response.status_code, 404)
        self.assertEqual(new_response.status_code, 200)

# feed does not expose notes
    def test_calendar_feed_does_not_include_notes_or_job_description(self):
        self.application.notes = "Private salary note"
        self.application.job_description = "Full confidential job description"
        self.application.save()

        response = self.client.get(self.get_feed_url())

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Private salary note")
        self.assertNotContains(response, "Full confidential job description")