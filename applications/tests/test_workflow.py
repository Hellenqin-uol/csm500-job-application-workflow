import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from applications.models import JobApplication, ApplicationEvent

class JobApplicationWorkflowTests(TestCase):
    # setup, create test users
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="testpass123"
        )

        self.other_user = User.objects.create_user(
            username="bob",
            password="testpass456"
        )

        self.application = JobApplication.objects.create(
            user=self.user,
            company_name="Muster GmbH",
            job_title="Backend Developer",
            status=JobApplication.Status.INTERESTED,
        )
    # Kanban requires login
    def test_kanban_requires_login(self):
        response = self.client.get(reverse("applications:kanban"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/account/login/", response.url)

    # Kanban shows user applications
    def test_kanban_shows_user_applications(self):
        self.client.login(username="alice", password="testpass123")

        response = self.client.get(reverse("applications:kanban"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backend Developer")
        self.assertContains(response, "Muster GmbH")

    # Kanban does not show other user applications
    def test_kanban_does_not_show_other_user_applications(self):
        JobApplication.objects.create(
            user=self.other_user,
            company_name="Secret Corp",
            job_title="Data Analyst",
            status=JobApplication.Status.INTERESTED,
        )

        self.client.login(username="alice", password="testpass123")

        response = self.client.get(reverse("applications:kanban"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backend Developer")
        self.assertNotContains(response, "Data Analyst")
        self.assertNotContains(response, "Secret Corp")

    # Status update via AJAX
    def test_status_update_changes_application_status(self):
        self.client.login(username="alice", password="testpass123")

        url = reverse(
            "applications:application_update_status",
            kwargs={"pk": self.application.pk}
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "status": JobApplication.Status.APPLIED
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.APPLIED
        )
    # Status update creates event
    def test_status_update_creates_status_changed_event(self):
        self.client.login(username="alice", password="testpass123")

        url = reverse(
            "applications:application_update_status",
            kwargs={"pk": self.application.pk}
        )

        self.client.post(
            url,
            data=json.dumps({
                "status": JobApplication.Status.APPLIED
            }),
            content_type="application/json"
        )

        event = ApplicationEvent.objects.filter(
            application=self.application,
            event_type=ApplicationEvent.EventType.STATUS_CHANGED
        ).first()

        self.assertIsNotNone(event)
        self.assertEqual(event.old_status, JobApplication.Status.INTERESTED)
        self.assertEqual(event.new_status, JobApplication.Status.APPLIED)

    # Other user cannot update application
    def test_user_cannot_update_other_users_application(self):
        login_success = self.client.login(username="bob", password="testpass456")
        self.assertTrue(login_success, "Bob cannot login")

        url = reverse(
            "applications:application_update_status",
            kwargs={"pk": self.application.pk}
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "status": JobApplication.Status.APPLIED
            }),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest" 
        )

        self.assertEqual(response.status_code, 404)

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.INTERESTED
        )
    # Invalid status is rejected
    def test_invalid_status_is_rejected(self):
        self.client.login(username="alice", password="testpass123")

        url = reverse(
            "applications:application_update_status",
            kwargs={"pk": self.application.pk}
        )

        response = self.client.post(
            url,
            data=json.dumps({
                "status": "not_a_real_status"
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.INTERESTED
        )
    # Archived applications are hidden from board
    def test_archived_applications_are_not_shown_on_board(self):
        self.application.status = JobApplication.Status.ARCHIVED
        self.application.save()

        self.client.login(username="alice", password="testpass123")

        response = self.client.get(reverse("applications:kanban"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Backend Developer")

    # Archived applications appear in archived view
    def test_archived_applications_appear_in_archived_view(self):
        self.application.status = JobApplication.Status.ARCHIVED
        self.application.save()

        self.client.login(username="alice", password="testpass123")

        response = self.client.get(reverse("applications:archived_applications"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backend Developer")

    # Archived applications can be unarchived and land in column interested
    def test_archived_application_can_be_restored_to_board(self):
        self.application.status = JobApplication.Status.ARCHIVED
        self.application.save()

        self.client.login(username="alice", password="testpass123")

        url = reverse("applications:application_unarchive", kwargs={"pk": self.application.pk})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)

        self.application.refresh_from_db()
        self.assertEqual(self.application.status, JobApplication.Status.INTERESTED)